"use client";

import { useEffect, useState, useCallback, useRef, useMemo, memo } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Clock, CreditCard, Zap, Plus, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { api } from "@/lib/api";
import type { CreditBalance, HistoryResponse, SessionSummary } from "@/lib/types";
import { getStatusConfig } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { staggerContainer, fadeUpItem } from "@/lib/motion";

/* ─── Credit ring ─── */
function CreditRing({ balance }: { balance: CreditBalance }) {
  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  const pct =
    balance.paid_minutes_total > 0
      ? balance.paid_minutes_remaining / balance.paid_minutes_total
      : 0;
  const offset = circumference - pct * circumference;

  return (
    <div className="relative w-28 h-28 shrink-0">
      <svg viewBox="0 0 112 112" className="w-full h-full -rotate-90">
        <circle
          cx="56"
          cy="56"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.04)"
          strokeWidth="7"
        />
        <motion.circle
          cx="56"
          cy="56"
          r={radius}
          fill="none"
          stroke="#E84A2F"
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ type: "spring", stiffness: 45, damping: 18, delay: 0.4 }}
          style={{ filter: "drop-shadow(0 0 10px rgba(232,74,47,0.5))" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white tabular-nums leading-none">
          {balance.total_available.toFixed(0)}
        </span>
        <span className="text-[9px] text-white/30 uppercase tracking-wider mt-1">
          min left
        </span>
      </div>
    </div>
  );
}

/* ─── Stat mini-card ─── */
function StatCard({
  icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  color: string;
}) {
  return (
    <div className={`glass-card rounded-xl p-4 border ${color}`}>
      <div className="flex items-center gap-2 mb-2 text-white/40">
        {icon}
        <span className="text-[10px] uppercase tracking-wider font-medium">{label}</span>
      </div>
      <p className="text-xl font-bold text-white tabular-nums">{value}</p>
      {sub && <p className="text-xs text-white/30 mt-0.5">{sub}</p>}
    </div>
  );
}

/* ─── Session row / card ─── */
const SessionRow = memo(function SessionRow({ session }: { session: SessionSummary }) {
  const router = useRouter();
  const statusConfig = getStatusConfig(session.status);
  const thumbUrl = session.video_id
    ? `https://img.youtube.com/vi/${session.video_id}/mqdefault.jpg`
    : null;
  const dateStr = new Date(session.created_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <motion.button
      variants={fadeUpItem}
      onClick={() => router.push(`/?session=${session.id}`)}
      className="w-full flex items-center gap-4 px-4 py-3.5 rounded-xl hover:bg-white/[0.03] transition-colors duration-200 group text-left"
    >
      {/* Thumbnail */}
      <div className="relative w-16 h-9 rounded-lg overflow-hidden shrink-0 bg-white/[0.04]">
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={session.video_title || "Video thumbnail"}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg
              className="w-4 h-4 text-white/20"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Title + meta */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white/75 group-hover:text-white transition-colors truncate">
          {session.video_title || "Untitled"}
        </p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] text-white/30">{session.niche}</span>
          {session.is_watermarked && (
            <span className="text-[9px] text-amber-400/50">· Watermarked</span>
          )}
        </div>
      </div>

      {/* Status badge */}
      <div className="shrink-0 flex items-center gap-2">
        <span
          className={`hidden sm:inline-flex text-[11px] px-2.5 py-0.5 rounded-full font-medium ${statusConfig.color}`}
        >
          {statusConfig.label}
        </span>
      </div>

      {/* Minutes */}
      <span className="hidden sm:block text-xs text-white/40 tabular-nums shrink-0 w-16 text-right">
        {session.minutes_charged.toFixed(1)} min
      </span>

      {/* Date */}
      <span className="text-xs text-white/30 tabular-nums shrink-0 hidden md:block">
        {dateStr}
      </span>
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

  if (authStatus === "loading") {
    return (
      <main className="pt-24 pb-12">
        <div className="max-w-5xl mx-auto px-6 space-y-6">
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </main>
    );
  }

  if (authStatus === "unauthenticated") return null;

  const totalPages = history ? Math.ceil(history.total / history.per_page) : 1;

  const filteredSessions = useMemo(
    () =>
      (history?.sessions ?? []).filter((s) =>
        s.video_title.toLowerCase().includes(debouncedSearch.toLowerCase())
      ),
    [history, debouncedSearch]
  );

  return (
    <main className="pt-24 pb-12">
      <div className="max-w-5xl mx-auto px-6">
        {/* Page header */}
        <motion.div
          className="flex items-center justify-between mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-white/40 text-sm mt-0.5">
              {session?.user?.name ? `Welcome back, ${session.user.name.split(" ")[0]}` : "Welcome back"}
            </p>
          </div>
          <Button asChild>
            <Link href="/">
              <Plus className="w-4 h-4" />
              New Video
            </Link>
          </Button>
        </motion.div>

        {/* Credit section */}
        <motion.div
          className="glass-card rounded-2xl p-6 mb-6"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
        >
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-[#E84A2F]" />
              <h2 className="text-sm font-semibold text-white/80">Credit Balance</h2>
            </div>
            <Button variant="secondary" size="sm" asChild>
              <Link href="/pricing">Top Up</Link>
            </Button>
          </div>

          {loadingBalance ? (
            <div className="flex items-center gap-6">
              <Skeleton className="w-28 h-28 rounded-full" />
              <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-20" />
                ))}
              </div>
            </div>
          ) : balance ? (
            <div className="flex flex-col sm:flex-row items-center gap-6">
              <CreditRing balance={balance} />
              <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-3 w-full">
                <StatCard
                  icon={<CreditCard className="w-3.5 h-3.5" />}
                  label="Subscription"
                  value={`${balance.paid_minutes_remaining.toFixed(1)}`}
                  sub={`of ${balance.paid_minutes_total.toFixed(0)} min`}
                  color="border-[#E84A2F]/20"
                />
                <StatCard
                  icon={<Zap className="w-3.5 h-3.5" />}
                  label="Pay-As-You-Go"
                  value={`${balance.payg_minutes_remaining.toFixed(1)}`}
                  sub="min (no expiry)"
                  color="border-[#E84A2F]/15"
                />
                <StatCard
                  icon={<Clock className="w-3.5 h-3.5" />}
                  label="Free"
                  value={`${balance.free_minutes_remaining.toFixed(1)}`}
                  sub={`of ${balance.free_minutes_total.toFixed(0)} min`}
                  color="border-white/[0.06]"
                />
              </div>
            </div>
          ) : (
            <p className="text-white/40 text-sm">Unable to load balance.</p>
          )}
        </motion.div>

        {/* Session History */}
        <motion.div
          className="glass-card rounded-2xl overflow-hidden"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          {/* History header + search */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 border-b border-white/[0.05]">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#E84A2F]" />
              <h2 className="text-sm font-semibold text-white/80">Session History</h2>
              {history && (
                <span className="text-[10px] text-white/25 ml-1">
                  ({history.total} total)
                </span>
              )}
            </div>
            {/* Search */}
            <div className="relative">
              <label htmlFor="session-search" className="sr-only">Filter sessions by title</label>
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/25 pointer-events-none" />
              <input
                id="session-search"
                type="text"
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="Filter by title..."
                className="w-full sm:w-52 pl-9 pr-3 py-2 text-xs bg-white/[0.04] border border-white/[0.06] rounded-lg text-white/70 placeholder-white/20 outline-none focus:border-[#E84A2F]/40 focus:ring-1 focus:ring-[#E84A2F]/20 transition-all"
              />
            </div>
          </div>

          {/* Content */}
          <div className="p-2">
            {loadingHistory ? (
              <div className="space-y-2 p-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-14 w-full" />
                ))}
              </div>
            ) : filteredSessions.length > 0 ? (
              <>
                {/* Column labels (desktop) */}
                <div className="hidden sm:grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 px-4 pb-1 pt-2 text-[10px] font-medium text-white/25 uppercase tracking-wider">
                  <span className="w-16">Preview</span>
                  <span>Title</span>
                  <span>Status</span>
                  <span className="w-16 text-right">Minutes</span>
                  <span className="w-24 text-right hidden md:block">Date</span>
                </div>

                <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="show"
                  className="divide-y divide-white/[0.03]"
                >
                  {filteredSessions.map((s) => (
                    <SessionRow key={s.id} session={s} />
                  ))}
                </motion.div>

                {search && filteredSessions.length === 0 && (
                  <p className="text-center text-xs text-white/30 py-8">
                    No sessions match &ldquo;{search}&rdquo;
                  </p>
                )}

                {/* Pagination */}
                {totalPages > 1 && !search && (
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/[0.05] px-3 pb-2">
                    <p className="text-xs text-white/30">
                      Page {page} of {totalPages}
                    </p>
                    <div className="flex items-center gap-2">
                      <button
                        disabled={page <= 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1 disabled:opacity-30"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                        Prev
                      </button>
                      <button
                        disabled={page >= totalPages}
                        onClick={() => setPage((p) => p + 1)}
                        className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1 disabled:opacity-30"
                      >
                        Next
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              /* Empty state */
              <div className="text-center py-16">
                <div className="w-16 h-16 rounded-2xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-8 h-8 text-white/15"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.2}
                      d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <p className="text-white/40 text-sm mb-1">
                  {search ? `No results for "${search}"` : "No sessions yet"}
                </p>
                {!search && (
                  <>
                    <p className="text-white/25 text-xs mb-6">
                      Analyze a YouTube video to get started
                    </p>
                    <Button asChild size="sm">
                      <Link href="/">
                        <Plus className="w-4 h-4" />
                        Analyze Your First Video
                      </Link>
                    </Button>
                  </>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </main>
  );
}
