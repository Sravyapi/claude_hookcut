"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Shield,
  Film,
  AlertCircle,
  BarChart3,
} from "lucide-react";
import { api } from "@/lib/api";
import { getStatusConfig } from "@/lib/constants";
import { useToast } from "@/components/ui/use-toast";
import type {
  AdminDashboard,
  AdminSessionSummary,
  NarmInsight,
} from "@/lib/types";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { staggerContainer, fadeUpItem } from "@/lib/motion";

/* ─── Stat card ─── */
function StatCard({
  emoji,
  label,
  value,
}: {
  emoji: string;
  label: string;
  value: number;
}) {
  return (
    <motion.div
      variants={fadeUpItem}
      className="glass-card rounded-2xl p-6"
    >
      <div className="text-3xl mb-3">{emoji}</div>
      <p className="text-3xl font-bold text-white tabular-nums">{value.toLocaleString()}</p>
      <p className="text-sm text-white/40 mt-1">{label}</p>
    </motion.div>
  );
}

/* ─── Confidence badge ─── */
function ConfidenceBadge({ confidence }: { confidence: number }) {
  if (confidence >= 0.7)
    return (
      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[--color-success]/15 text-emerald-300 border border-[--color-success]/25 font-medium">
        High ({(confidence * 100).toFixed(0)}%)
      </span>
    );
  if (confidence >= 0.4)
    return (
      <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/25 font-medium">
        Medium ({(confidence * 100).toFixed(0)}%)
      </span>
    );
  return (
    <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/50 border border-white/10 font-medium">
      Low ({(confidence * 100).toFixed(0)}%)
    </span>
  );
}

/* ─── Main ─── */
export default function AdminDashboardPage() {
  const { toast } = useToast();
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null);
  const [insights, setInsights] = useState<NarmInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [insightsLoading, setInsightsLoading] = useState(true);
  const [narmRunning, setNarmRunning] = useState(false);
  const [engineMode, setEngineMode] = useState<string>("llm_only");
  const [engineModeLoading, setEngineModeLoading] = useState(true);

  useEffect(() => {
    api
      .adminDashboard()
      .then(setDashboard)
      .catch((err) => {
        console.warn("Failed to load admin dashboard:", err);
        const detail = err?.message || err?.detail;
        toast({ title: "Error", description: detail ? `Failed to load dashboard statistics: ${detail}` : "Failed to load dashboard statistics.", variant: "destructive" });
      })
      .finally(() => setLoading(false));

    api
      .adminGetHookEngineMode()
      .then((data) => setEngineMode(data.mode))
      .catch(() => {})
      .finally(() => setEngineModeLoading(false));

    api
      .adminNarmInsights()
      .then((data) => setInsights(data.insights || []))
      .catch((err) => {
        console.warn("Failed to load NARM insights:", err);
        setInsights([]);
        const detail = err?.message || err?.detail;
        toast({ title: "Error", description: detail ? `Failed to load NARM insights: ${detail}` : "Failed to load NARM insights.", variant: "destructive" });
      })
      .finally(() => setInsightsLoading(false));
  }, [toast]);

  const handleNarmAnalyze = useCallback(async () => {
    setNarmRunning(true);
    try {
      const result = await api.adminNarmAnalyze();
      if (result.insights) {
        setInsights(result.insights);
      }
    } catch (err) {
      console.warn("NARM analysis failed:", err);
      const detail = (err as { message?: string; detail?: string })?.message || (err as { detail?: string })?.detail;
      toast({ title: "Error", description: detail ? `Failed to run NARM analysis: ${detail}` : "Failed to run NARM analysis.", variant: "destructive" });
    } finally {
      setNarmRunning(false);
    }
  }, [toast]);

  const handleEngineMode = useCallback(
    async (mode: string) => {
      try {
        const result = await api.adminSetHookEngineMode(mode);
        setEngineMode(result.mode);
        toast({ title: "Hook engine mode updated", description: `Now using: ${result.mode.replace(/_/g, " ")}` });
      } catch (err) {
        const detail = (err as { message?: string })?.message;
        toast({ title: "Error", description: detail || "Failed to update engine mode.", variant: "destructive" });
      }
    },
    [toast],
  );

  return (
    <div className="space-y-6">
      {/* ─── Page header ─── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-center gap-3"
      >
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[--color-primary]/10 text-[--color-primary] border border-[--color-primary]/20 font-semibold uppercase tracking-wider">
              <Shield className="w-3 h-3 inline-block mr-1 -mt-px" />Admin
            </span>
          </div>
          <p className="text-white/40 text-sm mt-0.5">
            Platform overview and analytics
          </p>
        </div>
      </motion.div>

      {/* ─── Stat cards ─── */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : dashboard ? (
        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
          variants={staggerContainer}
          initial="hidden"
          animate="show"
        >
          <StatCard emoji="👤" label="Total Users" value={dashboard.total_users} />
          <StatCard emoji="🎬" label="Total Sessions" value={dashboard.total_sessions} />
          <StatCard emoji="📱" label="Total Shorts" value={dashboard.total_shorts} />
          <StatCard emoji="💳" label="Active Subscriptions" value={dashboard.active_subscriptions} />
        </motion.div>
      ) : (
        <div className="glass-card rounded-2xl p-12 text-center">
          <AlertCircle className="w-10 h-10 text-[--color-error]/60 mx-auto mb-3" />
          <p className="text-white/40 text-sm">Unable to load dashboard data.</p>
          <p className="text-white/25 text-xs mt-1">Check your connection and try refreshing the page.</p>
        </div>
      )}

      {/* ─── Hook Engine Mode ─── */}
      <motion.div
        className="glass-card rounded-2xl p-6"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        <h2 className="text-sm font-semibold text-white/80 mb-1">
          Hook Engine Mode
        </h2>
        <p className="text-[11px] text-white/30 mb-4">
          Controls how hooks are identified. Admin-only — does not affect user-facing labels.
        </p>
        {engineModeLoading ? (
          <Skeleton className="h-10 w-full" />
        ) : (
          <div className="flex flex-wrap gap-2">
            {[
              { value: "llm_only", label: "LLM Only", desc: "Default — full AI analysis" },
              { value: "deterministic_only", label: "Deterministic Only", desc: "Keyword heuristics, no API calls" },
              { value: "llm_with_deterministic_fallback", label: "LLM + Fallback", desc: "Try LLM first, fall back to deterministic" },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleEngineMode(opt.value)}
                className={`px-4 py-2.5 rounded-xl text-left transition-all duration-200 border ${
                  engineMode === opt.value
                    ? "bg-[--color-primary]/15 border-[--color-primary]/40 text-white"
                    : "bg-white/[0.03] border-white/[0.06] text-white/50 hover:bg-white/[0.06] hover:text-white/70"
                }`}
              >
                <span className="text-xs font-medium block">{opt.label}</span>
                <span className="text-[10px] text-white/30 block mt-0.5">{opt.desc}</span>
              </button>
            ))}
          </div>
        )}
      </motion.div>

      {/* ─── Recent Sessions ─── */}
      <motion.div
        className="glass-card rounded-2xl overflow-hidden"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.15 }}
      >
        <div className="px-6 py-4 border-b border-white/[0.06]">
          <h2 className="text-sm font-semibold text-white/80">
            Recent Sessions
          </h2>
        </div>

        {loading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : dashboard && dashboard.recent_sessions.length > 0 ? (
          <div className="overflow-x-auto">
            {/* Table header */}
            <div className="grid grid-cols-[1.5fr_2fr_1fr_1fr_0.8fr_1fr] gap-4 px-6 py-3 text-[10px] font-medium text-white/25 uppercase tracking-wider border-b border-white/[0.05]">
              <span>User</span>
              <span>Video Title</span>
              <span>Niche</span>
              <span>Status</span>
              <span className="text-right">Minutes</span>
              <span className="text-right">Date</span>
            </div>

            {/* Table rows */}
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="show"
              className="divide-y divide-white/[0.05]"
            >
              {dashboard.recent_sessions.slice(0, 10).map((session: AdminSessionSummary) => {
                const statusConfig = getStatusConfig(session.status);
                const dateStr = new Date(session.created_at).toLocaleDateString(
                  undefined,
                  { month: "short", day: "numeric", year: "numeric" }
                );

                return (
                  <motion.div
                    key={session.id}
                    variants={fadeUpItem}
                    className="grid grid-cols-[1.5fr_2fr_1fr_1fr_0.8fr_1fr] gap-4 px-6 py-3 hover:bg-white/[0.02] transition-colors even:bg-white/[0.02]"
                  >
                    <span className="text-sm text-white/60 truncate">
                      {session.user_email}
                    </span>
                    <span className="text-sm text-white/70 truncate">
                      {session.video_title || "Untitled"}
                    </span>
                    <span className="text-xs text-white/40">{session.niche}</span>
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
                  </motion.div>
                );
              })}
            </motion.div>
          </div>
        ) : (
          <div className="py-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center mx-auto mb-4">
              <Film className="w-7 h-7 text-white/15" />
            </div>
            <p className="text-sm text-white/40 mb-1">No sessions yet</p>
            <p className="text-xs text-white/25">Sessions will appear here as users analyze videos.</p>
          </div>
        )}
      </motion.div>

      {/* ─── NARM Insights ─── */}
      <motion.div
        className="glass-card rounded-2xl overflow-hidden"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.25 }}
      >
        <div className="px-6 py-4 border-b border-white/[0.06] flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white/80">
              NARM Insights
            </h2>
            <p className="text-[11px] text-white/30 mt-0.5">
              Neural Analysis and Recommendation Module
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleNarmAnalyze}
            disabled={narmRunning}
          >
            {narmRunning ? "Running..." : "Run Analysis"}
          </Button>
        </div>

        <div className="p-6">
          {insightsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : insights.length > 0 ? (
            <motion.div
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
              variants={staggerContainer}
              initial="hidden"
              animate="show"
            >
              {insights.map((insight) => {
                const dateStr = new Date(insight.created_at).toLocaleDateString(
                  undefined,
                  { month: "short", day: "numeric", year: "numeric" }
                );

                return (
                  <motion.div
                    key={insight.id}
                    variants={fadeUpItem}
                    className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4"
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <h3 className="text-sm font-medium text-white/80">
                        {insight.title}
                      </h3>
                      <ConfidenceBadge confidence={insight.confidence} />
                    </div>
                    <p className="text-xs text-white/45 leading-relaxed mb-3">
                      {insight.content}
                    </p>
                    <div className="flex items-center gap-3 text-[10px] text-white/25">
                      <span className="uppercase tracking-wider">
                        {insight.insight_type}
                      </span>
                      <span>{dateStr}</span>
                      <span>{insight.time_range_days}d range</span>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          ) : (
            <div className="py-12 text-center">
              <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-7 h-7 text-white/15" />
              </div>
              <p className="text-sm text-white/40 mb-1">No insights available</p>
              <p className="text-xs text-white/25">
                Click &quot;Run Analysis&quot; to generate insights from session data.
              </p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
