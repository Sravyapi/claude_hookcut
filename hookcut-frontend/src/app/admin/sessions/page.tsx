"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "@/lib/api";
import { getStatusConfig } from "@/lib/constants";
import { useToast } from "@/components/ui/use-toast";
import type {
  AdminSessionSummary,
  AdminSessionList,
  AdminSessionDetail,
  Hook,
  Short,
} from "@/lib/types";
import { Skeleton } from "@/components/ui/skeleton";
import { staggerContainer, fadeUpItem } from "@/lib/motion";

/* ─── Constants ─── */
const STATUS_FILTERS = [
  "all",
  "pending",
  "analyzing",
  "hooks_ready",
  "generating_shorts",
  "completed",
  "failed",
] as const;

/* ─── Short status badge ─── */
function shortStatusBadge(status: string) {
  const s = status.toLowerCase();
  if (s === "ready")
    return "bg-emerald-500/15 text-emerald-300 border-emerald-500/25";
  if (s === "processing" || s === "downloading" || s === "uploading")
    return "bg-amber-500/15 text-amber-300 border-amber-500/25";
  if (s === "failed")
    return "bg-red-500/15 text-red-300 border-red-500/25";
  return "bg-white/5 text-white/50 border-white/10";
}

/* ─── Expanded Detail Panel ─── */
function SessionDetailPanel({
  sessionId,
}: {
  sessionId: string;
}) {
  const [detail, setDetail] = useState<AdminSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showTranscript, setShowTranscript] = useState(false);

  useEffect(() => {
    setLoading(true);
    api
      .adminSessionDetail(sessionId)
      .then(setDetail)
      .catch((err) => console.warn("Failed to load session detail:", err))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <div className="px-6 py-4 space-y-3">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="px-6 py-4">
        <p className="text-sm text-white/30">Failed to load session details.</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.3 }}
      className="overflow-hidden"
    >
      <div className="px-6 py-5 bg-white/[0.02] border-t border-white/[0.04] space-y-5">
        {/* ─── Hooks ─── */}
        <div>
          <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-3">
            Hooks ({detail.hooks.length})
          </h3>
          {detail.hooks.length > 0 ? (
            <div className="space-y-2">
              {detail.hooks.map((hook: Hook) => (
                <div
                  key={hook.id}
                  className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-bold text-violet-400 tabular-nums shrink-0 mt-0.5">
                      #{hook.rank}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/70 line-clamp-2">
                        {hook.hook_text}
                      </p>
                      <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/40 border border-white/10">
                          {hook.hook_type}
                        </span>
                        <span className="text-[10px] text-white/30">
                          {hook.start_time} - {hook.end_time}
                        </span>
                        <span className="text-[10px] text-white/30">
                          Attention:{" "}
                          <span className="text-violet-300 font-medium">
                            {(hook.attention_score * 100).toFixed(0)}%
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-white/25">No hooks found.</p>
          )}
        </div>

        {/* ─── Shorts ─── */}
        <div>
          <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-3">
            Shorts ({detail.shorts.length})
          </h3>
          {detail.shorts.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {detail.shorts.map((short: Short) => (
                <div
                  key={short.id}
                  className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${shortStatusBadge(short.status)}`}
                    >
                      {short.status}
                    </span>
                    {short.duration_seconds && (
                      <span className="text-[10px] text-white/30 tabular-nums">
                        {short.duration_seconds.toFixed(1)}s
                      </span>
                    )}
                  </div>
                  {short.cleaned_captions && (
                    <p className="text-xs text-white/40 truncate">
                      {short.cleaned_captions}
                    </p>
                  )}
                  {short.error_message && (
                    <p className="text-xs text-red-400/70 mt-1 truncate">
                      {short.error_message}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-white/25">No shorts generated.</p>
          )}
        </div>

        {/* ─── Transcript ─── */}
        {detail.transcript_text && (
          <div>
            <button
              onClick={() => setShowTranscript(!showTranscript)}
              className="flex items-center gap-2 text-xs font-semibold text-white/50 uppercase tracking-wider hover:text-white/70 transition-colors"
            >
              Transcript
              {showTranscript ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>
            <AnimatePresence>
              {showTranscript && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="mt-3 bg-white/[0.02] border border-white/[0.04] rounded-xl p-4 max-h-64 overflow-y-auto scrollbar-thin">
                    <p className="text-xs text-white/40 leading-relaxed whitespace-pre-wrap">
                      {detail.transcript_text}
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </motion.div>
  );
}

/* ─── Main ─── */
export default function AdminSessionsPage() {
  const { toast } = useToast();
  const [data, setData] = useState<AdminSessionList | null>(null);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchSessions = useCallback(async (p: number, status: string) => {
    setLoading(true);
    try {
      const result = await api.adminSessions(
        p,
        status === "all" ? undefined : status
      );
      setData(result);
    } catch (err) {
      console.warn("Failed to load sessions:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchSessions(page, statusFilter);
  }, [page, statusFilter, fetchSessions]);

  /* Reset page when filter changes */
  const handleFilterChange = (value: string) => {
    setStatusFilter(value);
    setPage(1);
    setExpandedId(null);
  };

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 1;

  const toggleExpand = (sessionId: string) => {
    setExpandedId(expandedId === sessionId ? null : sessionId);
  };

  return (
    <div className="space-y-6">
      {/* ─── Page header ─── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold text-white">Session Browser</h1>
          <p className="text-white/40 text-sm mt-0.5">
            Browse and inspect all analysis sessions
            {data && (
              <span className="text-white/25 ml-2">
                ({data.total} total)
              </span>
            )}
          </p>
        </div>

        {/* Status filter */}
        <div className="flex items-center gap-2">
          <label className="text-[10px] text-white/30 uppercase tracking-wider font-medium">
            Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => handleFilterChange(e.target.value)}
            className="appearance-none px-3 py-2 rounded-xl text-sm bg-white/[0.04] border border-white/[0.08] text-white/70 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all cursor-pointer"
          >
            {STATUS_FILTERS.map((s) => (
              <option
                key={s}
                value={s}
                className="bg-[#0a0a14] text-white"
              >
                {s === "all"
                  ? "All Statuses"
                  : s
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (c) => c.toUpperCase())}
              </option>
            ))}
          </select>
        </div>
      </motion.div>

      {/* ─── Sessions table ─── */}
      <motion.div
        className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        {loading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : data && data.sessions.length > 0 ? (
          <>
            {/* Table header */}
            <div className="grid grid-cols-[1.5fr_2fr_0.8fr_1fr_0.8fr_1fr_auto] gap-3 px-6 py-3 text-[10px] font-medium text-white/25 uppercase tracking-wider border-b border-white/[0.06]">
              <span>User Email</span>
              <span>Video Title</span>
              <span>Niche</span>
              <span>Status</span>
              <span className="text-right">Minutes</span>
              <span className="text-right">Date</span>
              <span className="w-6" />
            </div>

            {/* Table rows */}
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="show"
            >
              {data.sessions.map((session: AdminSessionSummary) => {
                const statusConfig = getStatusConfig(session.status);
                const dateStr = new Date(session.created_at).toLocaleDateString(
                  undefined,
                  { month: "short", day: "numeric", year: "numeric" }
                );
                const isExpanded = expandedId === session.id;

                return (
                  <motion.div key={session.id} variants={fadeUpItem}>
                    {/* Row */}
                    <button
                      onClick={() => toggleExpand(session.id)}
                      className="w-full grid grid-cols-[1.5fr_2fr_0.8fr_1fr_0.8fr_1fr_auto] gap-3 px-6 py-3.5 hover:bg-white/[0.02] transition-colors border-b border-white/[0.03] items-center text-left"
                    >
                      <span className="text-sm text-white/60 truncate">
                        {session.user_email}
                      </span>
                      <span className="text-sm text-white/70 truncate">
                        {session.video_title || "Untitled"}
                      </span>
                      <span className="text-xs text-white/40 truncate">
                        {session.niche}
                      </span>
                      <span>
                        <span
                          className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium ${statusConfig.color}`}
                        >
                          {statusConfig.label}
                        </span>
                      </span>
                      <span className="text-xs text-white/40 tabular-nums text-right">
                        {session.minutes_charged.toFixed(1)}
                      </span>
                      <span className="text-xs text-white/30 tabular-nums text-right">
                        {dateStr}
                      </span>
                      <span className="w-6 flex items-center justify-center">
                        <motion.div
                          animate={{ rotate: isExpanded ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ChevronDown className="w-3.5 h-3.5 text-white/25" />
                        </motion.div>
                      </span>
                    </button>

                    {/* Expanded detail */}
                    <AnimatePresence>
                      {isExpanded && (
                        <SessionDetailPanel sessionId={session.id} />
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })}
            </motion.div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-white/[0.06]">
                <p className="text-xs text-white/30">
                  Page {page} of {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-white/50 hover:text-white/70 bg-white/[0.04] border border-white/[0.06] hover:bg-white/[0.06] transition-colors disabled:opacity-30 disabled:pointer-events-none"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                    Previous
                  </button>
                  <button
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-white/50 hover:text-white/70 bg-white/[0.04] border border-white/[0.06] hover:bg-white/[0.06] transition-colors disabled:opacity-30 disabled:pointer-events-none"
                  >
                    Next
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="py-16 text-center">
            <p className="text-sm text-white/30">
              {statusFilter !== "all"
                ? `No sessions with status "${statusFilter.replace(/_/g, " ")}".`
                : "No sessions found."}
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
