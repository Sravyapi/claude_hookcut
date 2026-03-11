"use client";

import { useEffect, useState, useCallback, useRef, useMemo, memo } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Clock, CreditCard, Zap, Plus, ChevronLeft, ChevronRight, Search, Scissors, ArrowRight, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { CreditBalance, HistoryResponse, SessionSummary } from "@/lib/types";
import { getStatusConfig } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { staggerContainer, fadeUpItem } from "@/lib/motion";
import { youtubeThumbUrl } from "@/lib/utils";
import Header from "@/components/header";

/* ─── Credit ring ─── */
function CreditRing({ value, max, label }: { value: number; max: number; label: string }) {
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const pct = max > 0 ? value / max : 0;
  const offset = circumference - pct * circumference;

  return (
    <div className="relative w-24 h-24 shrink-0">
      <svg viewBox="0 0 96 96" className="w-full h-full -rotate-90">
        <circle
          cx="48" cy="48" r={radius}
          fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="6"
        />
        <motion.circle
          cx="48" cy="48" r={radius}
          fill="none" stroke="url(#ring-gradient)" strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ type: "spring", stiffness: 45, damping: 18, delay: 0.4 }}
        />
        <defs>
          <linearGradient id="ring-gradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#E84A2F" />
            <stop offset="100%" stopColor="#F97316" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white tabular-nums leading-none">
          {value.toFixed(0)}
        </span>
        <span className="text-[9px] text-white/30 uppercase tracking-wider mt-0.5">
          {label}
        </span>
      </div>
    </div>
  );
}

/* ─── Credit stat line ─── */
function CreditLine({ label, value, total, color }: { label: string; value: number; total?: number; color: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0">
      <div className="flex items-center gap-2">
        <div className={`w-1.5 h-1.5 rounded-full ${color}`} />
        <span className="text-xs text-white/50">{label}</span>
      </div>
      <span className="text-xs font-medium text-white/70 tabular-nums">
        {value.toFixed(1)}{total !== undefined ? <span className="text-white/25"> / {total.toFixed(0)}</span> : null} min
      </span>
    </div>
  );
}

/* ─── Session row ─── */
const SessionRow = memo(function SessionRow({ session }: { session: SessionSummary }) {
  const router = useRouter();
  const statusConfig = getStatusConfig(session.status);
  const thumbUrl = session.video_id ? youtubeThumbUrl(session.video_id) : null;
  const dateStr = new Date(session.created_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });

  return (
    <motion.button
      variants={fadeUpItem}
      onClick={() => router.push(`/?session=${session.id}`)}
      className="w-full flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-white/[0.04] transition-all duration-200 group text-left"
    >
      {/* Thumbnail */}
      <div className="relative w-14 h-8 rounded-lg overflow-hidden shrink-0 bg-white/[0.04]">
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={session.video_title || "Video thumbnail"}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-white/15" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            </svg>
          </div>
        )}
      </div>

      {/* Title + meta */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white/70 group-hover:text-white transition-colors truncate">
          {session.video_title || "Untitled"}
        </p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] text-white/25">{dateStr}</span>
          <span className="text-[10px] text-white/15">·</span>
          <span className="text-[10px] text-white/25">{session.niche}</span>
        </div>
      </div>

      {/* Status badge */}
      <span className={`hidden sm:inline-flex text-[10px] px-2 py-0.5 rounded-full font-medium ${statusConfig.color}`}>
        {statusConfig.label}
      </span>

      {/* Minutes */}
      <span className="hidden sm:block text-xs text-white/30 tabular-nums shrink-0 w-14 text-right">
        {(session.minutes_charged ?? 0).toFixed(1)}m
      </span>

      <ArrowRight className="w-3.5 h-3.5 text-white/10 group-hover:text-white/30 transition-colors shrink-0" />
    </motion.button>
  );
});

/* ─── Main page ─── */
export default function DashboardPage() {
  const { data: session, status: authStatus } = useSession();
  const router = useRouter();

  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loadingBalance, setLoadingBalance] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => setDebouncedSearch(value), 250);
  }, []);

  useEffect(() => {
    return () => { if (searchTimerRef.current) clearTimeout(searchTimerRef.current); };
  }, []);

  useEffect(() => {
    if (authStatus === "unauthenticated") router.push("/auth/login");
  }, [authStatus, router]);

  useEffect(() => {
    if (authStatus !== "authenticated") return;
    setLoadingBalance(true);
    api
      .getBalance()
      .then(setBalance)
      .catch((err) => console.warn("Failed to load balance:", err))
      .finally(() => setLoadingBalance(false));
  }, [authStatus]);

  const fetchHistory = useCallback(
    async (p: number) => {
      setLoadingHistory(true);
      try {
        const data = await api.getHistory(p);
        setHistory(data);
      } catch (err) {
        console.warn("Failed to load history:", err);
      } finally {
        setLoadingHistory(false);
      }
    },
    []
  );

  useEffect(() => {
    if (authStatus !== "authenticated") return;
    fetchHistory(page);
  }, [authStatus, page, fetchHistory]);

  const totalPages = history ? Math.ceil(history.total / history.per_page) : 1;

  const filteredSessions = useMemo(
    () =>
      (history?.sessions ?? []).filter((s) =>
        s.video_title.toLowerCase().includes(debouncedSearch.toLowerCase())
      ),
    [history, debouncedSearch]
  );

  const totalMinutes = balance ? balance.total_available : 0;
  const hasAiMinutes = balance ? (balance.paid_minutes_remaining + balance.free_minutes_remaining + balance.payg_minutes_remaining) > 0 : false;
  const hasClipMinutes = balance ? balance.manual_clip_minutes_remaining > 0 : false;
  const firstName = session?.user?.name?.split(" ")[0];

  if (authStatus === "loading") {
    return (
      <>
        <Header />
        <main className="pt-24 pb-12">
          <div className="max-w-4xl mx-auto px-6 space-y-6">
            <Skeleton className="h-32 w-full rounded-2xl" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Skeleton className="h-48 rounded-2xl" />
              <Skeleton className="h-48 rounded-2xl" />
            </div>
            <Skeleton className="h-64 w-full rounded-2xl" />
          </div>
        </main>
      </>
    );
  }

  if (authStatus === "unauthenticated") return null;

  return (
    <>
    <Header />
    <main className="pt-24 pb-12">
      <div className="max-w-4xl mx-auto px-6">

        {/* ─── Hero greeting ─── */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 className="text-2xl font-bold text-white">
            {firstName ? `Welcome back, ${firstName}` : "Welcome back"}
          </h1>
          <p className="text-white/35 text-sm mt-1">
            {history && history.total > 0
              ? `You have ${history.total} session${history.total === 1 ? "" : "s"}`
              : "Get started by analyzing your first video"
            }
          </p>
        </motion.div>

        {/* ─── Quick action cards ─── */}
        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
        >
          {/* AI Analysis card */}
          <Link
            href={hasAiMinutes ? "/?new=1" : "/pricing"}
            className="glass-card rounded-2xl p-5 group hover:border-[#E84A2F]/20 transition-all duration-300 block"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#E84A2F]/20 to-orange-500/10 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-[#E84A2F]" />
              </div>
              <ArrowRight className="w-4 h-4 text-white/15 group-hover:text-white/40 group-hover:translate-x-0.5 transition-all" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-0.5">AI Analysis</h3>
            <p className="text-xs text-white/35">
              {hasAiMinutes
                ? `${(balance!.paid_minutes_remaining + balance!.free_minutes_remaining + balance!.payg_minutes_remaining).toFixed(0)} min available`
                : "Top up to get started"
              }
            </p>
          </Link>

          {/* Manual Clip card */}
          <Link
            href={hasClipMinutes ? "/clip" : "/pricing"}
            className="glass-card rounded-2xl p-5 group hover:border-violet-500/20 transition-all duration-300 block"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/10 flex items-center justify-center">
                <Scissors className="w-5 h-5 text-violet-400" />
              </div>
              <ArrowRight className="w-4 h-4 text-white/15 group-hover:text-white/40 group-hover:translate-x-0.5 transition-all" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-0.5">Manual Clip</h3>
            <p className="text-xs text-white/35">
              {hasClipMinutes
                ? `${balance!.manual_clip_minutes_remaining.toFixed(0)} min available`
                : "Top up to get started"
              }
            </p>
          </Link>
        </motion.div>

        {/* ─── Credits + History row ─── */}
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">

          {/* Credit Balance sidebar */}
          <motion.div
            className="glass-card rounded-2xl p-5"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs font-semibold text-white/50 uppercase tracking-wider">Credits</h2>
              <Link
                href="/pricing"
                className="text-[10px] font-medium text-[#E84A2F] hover:text-[#E84A2F]/80 transition-colors"
              >
                Top Up
              </Link>
            </div>

            {loadingBalance ? (
              <div className="space-y-3">
                <Skeleton className="w-24 h-24 rounded-full mx-auto" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
              </div>
            ) : balance ? (
              <>
                <div className="flex justify-center mb-4">
                  <CreditRing value={totalMinutes} max={Math.max(totalMinutes, balance.free_minutes_total)} label="min left" />
                </div>
                <div className="space-y-0">
                  {balance.free_minutes_remaining > 0 && (
                    <CreditLine label="Free" value={balance.free_minutes_remaining} total={balance.free_minutes_total} color="bg-white/30" />
                  )}
                  {balance.paid_minutes_total > 0 && (
                    <CreditLine label="Subscription" value={balance.paid_minutes_remaining} total={balance.paid_minutes_total} color="bg-[#E84A2F]" />
                  )}
                  {balance.payg_minutes_remaining > 0 && (
                    <CreditLine label="Pay-As-You-Go" value={balance.payg_minutes_remaining} color="bg-amber-400" />
                  )}
                  {balance.manual_clip_minutes_total > 0 && (
                    <CreditLine label="Manual Clips" value={balance.manual_clip_minutes_remaining} total={balance.manual_clip_minutes_total} color="bg-violet-400" />
                  )}
                </div>
              </>
            ) : (
              <p className="text-white/30 text-xs text-center py-4">Unable to load</p>
            )}
          </motion.div>

          {/* Session History */}
          <motion.div
            className="glass-card rounded-2xl overflow-hidden"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.15 }}
          >
            {/* History header + search */}
            <div className="flex items-center justify-between gap-3 p-4 border-b border-white/[0.04]">
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-semibold text-white/50 uppercase tracking-wider">History</h2>
                {history && history.total > 0 && (
                  <span className="text-[10px] text-white/20 tabular-nums">{history.total}</span>
                )}
              </div>
              {history && history.total > 0 && (
                <div className="relative">
                  <label htmlFor="session-search" className="sr-only">Filter sessions by title</label>
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-white/20 pointer-events-none" />
                  <input
                    id="session-search"
                    type="text"
                    value={search}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    placeholder="Search..."
                    className="w-36 pl-7 pr-2.5 py-1.5 text-[11px] bg-white/[0.04] border border-white/[0.06] rounded-lg text-white/60 placeholder-white/15 outline-none focus:border-[#E84A2F]/30 transition-all"
                  />
                </div>
              )}
            </div>

            {/* Content */}
            <div className="p-1.5">
              {loadingHistory ? (
                <div className="space-y-1.5 p-2">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full rounded-xl" />
                  ))}
                </div>
              ) : filteredSessions.length > 0 ? (
                <>
                  <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="show"
                  >
                    {filteredSessions.map((s) => (
                      <SessionRow key={s.id} session={s} />
                    ))}
                  </motion.div>

                  {search && filteredSessions.length === 0 && (
                    <p className="text-center text-xs text-white/25 py-8">
                      No results for &ldquo;{search}&rdquo;
                    </p>
                  )}

                  {/* Pagination */}
                  {totalPages > 1 && !search && (
                    <div className="flex items-center justify-between mt-2 pt-3 border-t border-white/[0.04] px-3 pb-2">
                      <p className="text-[11px] text-white/25 tabular-nums">
                        {page} / {totalPages}
                      </p>
                      <div className="flex items-center gap-1.5">
                        <button
                          disabled={page <= 1}
                          onClick={() => setPage((p) => Math.max(1, p - 1))}
                          className="p-1.5 rounded-lg hover:bg-white/[0.05] disabled:opacity-20 transition-colors"
                          aria-label="Previous page"
                        >
                          <ChevronLeft className="w-3.5 h-3.5 text-white/40" />
                        </button>
                        <button
                          disabled={page >= totalPages}
                          onClick={() => setPage((p) => p + 1)}
                          className="p-1.5 rounded-lg hover:bg-white/[0.05] disabled:opacity-20 transition-colors"
                          aria-label="Next page"
                        >
                          <ChevronRight className="w-3.5 h-3.5 text-white/40" />
                        </button>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                /* Empty state */
                <div className="text-center py-16 px-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#E84A2F]/10 to-orange-500/5 border border-white/[0.04] flex items-center justify-center mx-auto mb-3">
                    <Plus className="w-5 h-5 text-[#E84A2F]/50" />
                  </div>
                  <p className="text-white/40 text-sm mb-1">
                    {search ? `No results for "${search}"` : "No sessions yet"}
                  </p>
                  {!search && (
                    <>
                      <p className="text-white/20 text-xs mb-5">
                        Paste a YouTube URL to find viral hooks
                      </p>
                      <Button asChild size="sm">
                        <Link href="/?new=1">
                          <Sparkles className="w-3.5 h-3.5" />
                          Analyze a Video
                        </Link>
                      </Button>
                    </>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </main>
    </>
  );
}
