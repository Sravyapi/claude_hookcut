"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Clock, Zap, Settings } from "lucide-react";
import { api } from "@/lib/api";
import type { CreditBalance, SessionSummary } from "@/lib/types";
import { getStatusConfig } from "@/lib/constants";
import { HeroUrlInput } from "@/components/hero-url-input";
import { Footer } from "@/components/footer";
import { useUser } from "@/components/providers";
import { youtubeThumbUrl } from "@/lib/utils";

export function AuthenticatedHome() {
  const { data: session } = useSession();
  const { role } = useUser();
  const isAdmin = role === "admin";
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [recentSessions, setRecentSessions] = useState<SessionSummary[]>([]);
  const [engineMode, setEngineMode] = useState<string>("llm_only");
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    api.getBalance().then((b) => { if (mountedRef.current) setBalance(b); }).catch(() => undefined);
    api
      .getHistory(1)
      .then((h) => { if (mountedRef.current) setRecentSessions(h.sessions.slice(0, 3)); })
      .catch(() => undefined);
    if (isAdmin) {
      api.adminGetHookEngineMode().then((d) => {
        if (mountedRef.current) setEngineMode(d.mode);
      }).catch(() => undefined);
    }
    return () => { mountedRef.current = false; };
  }, [isAdmin]);

  const handleEngineMode = useCallback(async (mode: string) => {
    const prev = engineMode;
    setEngineMode(mode);
    try {
      const result = await api.adminSetHookEngineMode(mode);
      setEngineMode(result.mode);
    } catch {
      setEngineMode(prev);
    }
  }, [engineMode]);

  const firstName = session?.user?.name?.split(" ")[0] ?? "there";

  return (
    <>
      <main id="main-content" className="pt-24 pb-16 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Greeting */}
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-3">
              Hey {firstName}, ready to find hooks?
            </h1>
            <p className="text-white/35 text-base">
              Paste any YouTube URL below to extract the most engaging moments.
            </p>
          </motion.div>

          {/* Admin: Hook Engine Mode toggle */}
          {isAdmin && (
            <motion.div
              className="mb-6 bg-white/[0.03] border border-white/[0.06] rounded-xl p-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.05 }}
            >
              <div className="flex items-center gap-2 mb-3">
                <Settings className="w-3.5 h-3.5 text-white/30" />
                <span className="text-xs font-medium text-white/40 uppercase tracking-wider">
                  Hook Engine
                </span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#E84A2F]/15 text-[#E84A2F]/70 font-medium">
                  Admin
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {[
                  { value: "llm_only", label: "LLM Only" },
                  { value: "deterministic_only", label: "Deterministic" },
                  { value: "llm_with_deterministic_fallback", label: "LLM + Fallback" },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleEngineMode(opt.value)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 border ${
                      engineMode === opt.value
                        ? "bg-[#E84A2F]/15 border-[#E84A2F]/40 text-white"
                        : "bg-white/[0.02] border-white/[0.06] text-white/40 hover:text-white/60"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* URL Input */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <HeroUrlInput />
          </motion.div>

          {/* Quick stats */}
          {balance && (
            <motion.div
              className="flex items-center justify-center gap-6 mt-8"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.25 }}
            >
              <div className="flex items-center gap-2 text-sm text-white/40">
                <Zap className="w-3.5 h-3.5 text-[#E84A2F]" />
                <span className="font-mono tabular-nums text-white/70">
                  {balance.total_available.toFixed(0)}
                </span>
                <span>min remaining</span>
              </div>
              <Link
                href="/dashboard"
                className="text-sm text-white/30 hover:text-white/50 transition-colors underline underline-offset-2"
              >
                View dashboard
              </Link>
            </motion.div>
          )}

          {/* Recent sessions */}
          {recentSessions.length > 0 && (
            <motion.div
              className="mt-14"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-white/25" />
                  <h2 className="text-xs font-medium text-white/30 uppercase tracking-wider">
                    Recent
                  </h2>
                </div>
                <Link
                  href="/dashboard"
                  className="text-xs text-white/25 hover:text-white/40 transition-colors"
                >
                  See all
                </Link>
              </div>
              <div className="space-y-1">
                {recentSessions.map((s) => {
                  const statusConfig = getStatusConfig(s.status);
                  const thumbUrl = s.video_id
                    ? youtubeThumbUrl(s.video_id)
                    : null;
                  return (
                    <Link
                      key={s.id}
                      href={`/?session=${s.id}`}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/[0.03] transition-colors group"
                    >
                      <div className="w-14 h-8 rounded-lg overflow-hidden shrink-0 bg-white/[0.04]">
                        {thumbUrl && (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={thumbUrl}
                            alt=""
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = "none";
                            }}
                          />
                        )}
                      </div>
                      <p className="flex-1 text-sm text-white/50 group-hover:text-white/70 transition-colors truncate">
                        {s.video_title || "Untitled"}
                      </p>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${statusConfig.color}`}
                      >
                        {statusConfig.label}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </motion.div>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}
