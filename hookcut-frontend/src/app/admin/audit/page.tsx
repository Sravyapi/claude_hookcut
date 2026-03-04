"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Download,
  Filter,
} from "lucide-react";
import { api } from "@/lib/api";
import type { AuditLog, AuditLogList } from "@/lib/types";
import { useToast } from "@/components/ui/use-toast";
import { staggerContainer, fadeUpItem } from "@/lib/motion";

/* ─── Constants ─── */

const ACTION_FILTERS = [
  { value: "", label: "All" },
  { value: "role_changed", label: "Role Changed" },
  { value: "prompt_rule_created", label: "Rule Created" },
  { value: "prompt_rule_updated", label: "Rule Updated" },
  { value: "prompt_rule_reverted", label: "Rule Reverted" },
  { value: "prompt_rule_deleted", label: "Rule Deleted" },
  { value: "provider_updated", label: "Provider Updated" },
  { value: "provider_primary_changed", label: "Primary Changed" },
  { value: "api_key_updated", label: "API Key Updated" },
  { value: "narm_triggered", label: "NARM Triggered" },
];

const ACTION_COLORS: Record<string, string> = {
  role_changed: "bg-purple-500/15 text-purple-300 border-purple-500/25",
  prompt_rule_created: "bg-emerald-500/15 text-emerald-300 border-emerald-500/25",
  prompt_rule_updated: "bg-blue-500/15 text-blue-300 border-blue-500/25",
  prompt_rule_reverted: "bg-amber-500/15 text-amber-300 border-amber-500/25",
  prompt_rule_deleted: "bg-red-500/15 text-red-300 border-red-500/25",
  provider_updated: "bg-cyan-500/15 text-cyan-300 border-cyan-500/25",
  provider_primary_changed: "bg-violet-500/15 text-violet-300 border-violet-500/25",
  api_key_updated: "bg-yellow-500/15 text-yellow-300 border-yellow-500/25",
  narm_triggered: "bg-pink-500/15 text-pink-300 border-pink-500/25",
};

function getActionColor(action: string) {
  return (
    ACTION_COLORS[action] || "bg-white/5 text-white/50 border-white/10"
  );
}

/* ─── Audit Row ─── */

function AuditRow({ log }: { log: AuditLog }) {
  const [expanded, setExpanded] = useState(false);

  const dateStr = new Date(log.created_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const actionLabel = log.action
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  return (
    <motion.div variants={fadeUpItem}>
      <button
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        aria-label={expanded ? "Collapse audit log details" : "Expand audit log details"}
        className="w-full text-left hover:bg-white/[0.02] transition-colors"
      >
        {/* Desktop table row */}
        <div className="hidden md:grid grid-cols-[1.5fr_1fr_0.8fr_2fr_1fr_auto] gap-4 items-center px-5 py-3.5 border-b border-white/[0.04]">
          <span className="text-sm text-white/60 truncate">
            {log.admin_email}
          </span>
          <span
            className={`text-[11px] px-2.5 py-1 rounded-full border font-medium w-fit ${getActionColor(
              log.action
            )}`}
          >
            {actionLabel}
          </span>
          <span className="text-xs text-white/40 truncate">
            {log.resource_type}
          </span>
          <span className="text-xs text-white/50 truncate">
            {log.description}
          </span>
          <span className="text-xs text-white/30 tabular-nums">{dateStr}</span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-white/20 shrink-0" />
          ) : (
            <ChevronDown className="w-4 h-4 text-white/20 shrink-0" />
          )}
        </div>

        {/* Mobile card row */}
        <div className="md:hidden px-4 py-3 border-b border-white/[0.04]">
          <div className="flex items-center justify-between mb-2">
            <span
              className={`text-[11px] px-2.5 py-1 rounded-full border font-medium ${getActionColor(
                log.action
              )}`}
            >
              {actionLabel}
            </span>
            <span className="text-[11px] text-white/30 tabular-nums">
              {dateStr}
            </span>
          </div>
          <p className="text-sm text-white/60 truncate mb-1">
            {log.admin_email}
          </p>
          <p className="text-xs text-white/40 truncate">{log.description}</p>
        </div>
      </button>

      {/* Expanded detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-b border-white/[0.04]"
          >
            <div className="px-5 py-4 bg-white/[0.01]">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Before state */}
                <div>
                  <p className="text-xs font-medium text-white/40 mb-2">
                    Before State
                  </p>
                  {log.before_state ? (
                    <pre className="bg-black/30 rounded-lg p-4 text-xs font-mono overflow-x-auto max-h-48 overflow-y-auto text-white/50">
                      {JSON.stringify(log.before_state, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-xs text-white/20 italic px-4 py-3 bg-black/20 rounded-lg">
                      No previous state
                    </p>
                  )}
                </div>

                {/* After state */}
                <div>
                  <p className="text-xs font-medium text-white/40 mb-2">
                    After State
                  </p>
                  {log.after_state ? (
                    <pre className="bg-black/30 rounded-lg p-4 text-xs font-mono overflow-x-auto max-h-48 overflow-y-auto text-white/50">
                      {JSON.stringify(log.after_state, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-xs text-white/20 italic px-4 py-3 bg-black/20 rounded-lg">
                      No resulting state
                    </p>
                  )}
                </div>
              </div>

              {/* Additional metadata */}
              {log.resource_id && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-[11px] text-white/30">
                    Resource ID:
                  </span>
                  <span className="text-[11px] text-white/50 font-mono">
                    {log.resource_id}
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/* ─── Main Page ─── */

export default function AuditLogPage() {
  const { toast } = useToast();
  const [data, setData] = useState<AuditLogList | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState("");
  const [exporting, setExporting] = useState(false);

  const fetchLogs = useCallback(async (p: number, action: string) => {
    setLoading(true);
    try {
      const result = await api.adminAuditLogs(
        p,
        action || undefined
      );
      setData(result);
    } catch (err) {
      console.warn("Failed to load audit logs:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchLogs(page, actionFilter);
  }, [page, actionFilter, fetchLogs]);

  const handleFilterChange = (newFilter: string) => {
    setActionFilter(newFilter);
    setPage(1);
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      // Fetch all logs without pagination filter
      const allData = await api.adminAuditLogs(undefined, actionFilter || undefined);
      const blob = new Blob([JSON.stringify(allData.logs, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `audit-logs-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.warn("Failed to export audit logs:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setExporting(false);
    }
  };

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 1;

  return (
    <div className="space-y-6">
        {/* Header */}
        <motion.div
          className="flex items-center justify-between mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <FileText className="w-6 h-6 text-violet-400" />
              Audit Logs
            </h1>
            <p className="text-white/40 text-sm mt-0.5">
              Track all administrative actions across the system
            </p>
          </div>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/5 text-white/60 border border-white/10 hover:bg-white/[0.08] hover:text-white/80 transition-all duration-200 text-sm font-medium disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            {exporting ? "Exporting..." : "Export"}
          </button>
        </motion.div>

        {/* Filters */}
        <motion.div
          className="mb-6"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
        >
          <div className="flex items-center gap-3">
            <Filter className="w-4 h-4 text-white/30 shrink-0" />
            <select
              value={actionFilter}
              onChange={(e) => handleFilterChange(e.target.value)}
              className="px-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm text-white/70 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all appearance-none cursor-pointer min-w-[200px]"
            >
              {ACTION_FILTERS.map((f) => (
                <option
                  key={f.value}
                  value={f.value}
                  className="bg-zinc-900 text-white"
                >
                  {f.label}
                </option>
              ))}
            </select>
            {data && (
              <span className="text-[11px] text-white/25">
                {data.total} total log{data.total !== 1 ? "s" : ""}
              </span>
            )}
          </div>
        </motion.div>

        {/* Table */}
        <motion.div
          className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          {/* Table header (desktop) */}
          <div className="hidden md:grid grid-cols-[1.5fr_1fr_0.8fr_2fr_1fr_auto] gap-4 items-center px-5 py-3 border-b border-white/[0.06] bg-white/[0.02]">
            <span className="text-[10px] font-medium text-white/30 uppercase tracking-wider">
              Admin Email
            </span>
            <span className="text-[10px] font-medium text-white/30 uppercase tracking-wider">
              Action
            </span>
            <span className="text-[10px] font-medium text-white/30 uppercase tracking-wider">
              Resource
            </span>
            <span className="text-[10px] font-medium text-white/30 uppercase tracking-wider">
              Description
            </span>
            <span className="text-[10px] font-medium text-white/30 uppercase tracking-wider">
              Date
            </span>
            <span className="w-4" />
          </div>

          {/* Content */}
          {loading ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className="h-12 bg-white/[0.03] rounded-xl animate-pulse"
                />
              ))}
            </div>
          ) : data && data.logs.length > 0 ? (
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="show"
            >
              {data.logs.map((log) => (
                <AuditRow key={log.id} log={log} />
              ))}
            </motion.div>
          ) : (
            <div className="text-center py-16">
              <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center mx-auto mb-4">
                <FileText className="w-7 h-7 text-white/15" />
              </div>
              <p className="text-white/40 text-sm mb-1">No audit logs found</p>
              <p className="text-white/25 text-xs">
                {actionFilter
                  ? "Try a different filter or clear the filter to see all logs"
                  : "Administrative actions will appear here as they occur"}
              </p>
            </div>
          )}

          {/* Pagination */}
          {data && totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-4 border-t border-white/[0.05]">
              <p className="text-xs text-white/30">
                Page {page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-white/50 border border-white/[0.06] hover:bg-white/[0.04] hover:text-white/70 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  Prev
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-white/50 border border-white/[0.06] hover:bg-white/[0.04] hover:text-white/70 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </motion.div>
    </div>
  );
}
