"use client";

import { memo, useState, useCallback, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import type { VideoMeta } from "../lib/types";
import { api } from "../lib/api";
import { NICHES } from "../lib/constants";
import { formatDuration } from "../lib/utils";

// ── Types ─────────────────────────────────────────────────────────────────────

interface MarketingHomeProps {
  onAnalyze: (url: string, niche: string, language: string, meta: VideoMeta) => void;
}

// ── Demo constants ────────────────────────────────────────────────────────────

const DEMO_VIDEO_TITLE = "How I Got 1M Views on YouTube (Full Strategy)";
const DEMO_VIDEO_DURATION = "18:47";
const DEMO_URL_TEXT = "youtube.com/watch?v=xK3FoA2L9pQ";

const DEMO_HOOKS = [
  {
    score: 9.2,
    type: "CURIOSITY GAP",
    timestamp: "0:14",
    text: "Nobody talks about this YouTube trick that tripled my views overnight...",
    color: "#E84A2F",
  },
  {
    score: 8.5,
    type: "FEAR-BASED",
    timestamp: "2:31",
    text: "I tested 47 AI tools and what I found will change how you post forever...",
    color: "#F59E0B",
  },
  {
    score: 7.8,
    type: "CONTRARIAN",
    timestamp: "4:07",
    text: "Everyone is wrong about what makes a Short go viral in 2025...",
    color: "#10B981",
  },
] as const;

const TICKER_ITEMS = [
  "10,000+ hooks analyzed",
  "Used by 2,000+ creators",
  "4.8★ from real creators",
  "Results in ~2 minutes",
  "120 free minutes on signup",
  "No credit card required",
  "#1 hook finder for YouTube",
  "Built for Indian creators",
] as const;

// Seeded waveform bars for consistent render (no hydration mismatch)
const WAVEFORM_BARS = Array.from({ length: 48 }, (_, i) => {
  const seed = (i * 7919 + 13) % 100;
  return 20 + (seed % 65);
});

type DemoPhase = "video" | "entering" | "analyzing" | "results" | "exit";

// ── Score ring ────────────────────────────────────────────────────────────────

function ScoreRing({
  score,
  color,
  size = 52,
}: {
  score: number;
  color: string;
  size?: number;
}) {
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const dashOffset = circ - (score / 10) * circ;
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90"
        aria-hidden="true"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="4"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: dashOffset }}
          transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span
          className="font-mono font-bold text-white"
          style={{ fontSize: size * 0.28 }}
        >
          {score.toFixed(1)}
        </span>
      </div>
    </div>
  );
}

// ── Waveform scan ─────────────────────────────────────────────────────────────

function WaveformScan({ active }: { active: boolean }) {
  return (
    <div className="relative h-12 flex items-end gap-[2px] overflow-hidden rounded-lg">
      {WAVEFORM_BARS.map((h, i) => (
        <div
          key={i}
          className="rounded-sm flex-1"
          style={{
            height: `${h}%`,
            background: active
              ? `rgba(232, 74, 47, ${0.25 + (h / 100) * 0.55})`
              : "rgba(255,255,255,0.1)",
            transition: `background 0.08s ease ${i * 0.01}s`,
          }}
        />
      ))}
      {active && (
        <motion.div
          className="absolute top-0 bottom-0 w-0.5 bg-[#E84A2F]"
          style={{ boxShadow: "0 0 10px #E84A2F, 0 0 20px rgba(232,74,47,0.4)" }}
          initial={{ left: "0%" }}
          animate={{ left: "100%" }}
          transition={{ duration: 2, ease: "linear" }}
        />
      )}
    </div>
  );
}

// ── Demo hook card ────────────────────────────────────────────────────────────

function DemoHookCard({
  hook,
  index,
}: {
  hook: (typeof DEMO_HOOKS)[number];
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1], delay: index * 0.14 }}
      className="flex items-center gap-4 rounded-2xl border border-white/[0.07] bg-[#141414] px-5 py-4"
    >
      <ScoreRing score={hook.score} color={hook.color} size={52} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
          <span
            className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full"
            style={{
              color: hook.color,
              background: `${hook.color}18`,
              border: `1px solid ${hook.color}30`,
            }}
          >
            {hook.type}
          </span>
          <span className="text-[10px] font-mono text-white/25">{hook.timestamp}</span>
        </div>
        <p className="text-[13px] text-white/55 leading-relaxed line-clamp-2">{hook.text}</p>
      </div>
    </motion.div>
  );
}

// ── Hero demo (auto-playing animation) ───────────────────────────────────────

function HeroDemo() {
  const [phase, setPhase] = useState<DemoPhase>("video");
  const [typedChars, setTypedChars] = useState(0);
  const mountedRef = useRef(true);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const schedule = useCallback((fn: () => void, delay: number) => {
    timerRef.current = setTimeout(fn, delay);
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    const safe = (fn: () => void) => () => {
      if (mountedRef.current) fn();
    };

    const run = () => {
      if (!mountedRef.current) return;
      setPhase("video");
      setTypedChars(0);

      schedule(
        safe(() => {
          setPhase("entering");
          let i = 0;
          const typeNext = () => {
            if (!mountedRef.current) return;
            i++;
            setTypedChars(i);
            if (i < DEMO_URL_TEXT.length) {
              timerRef.current = setTimeout(typeNext, 44);
            } else {
              schedule(
                safe(() => {
                  setPhase("analyzing");
                  schedule(
                    safe(() => {
                      setPhase("results");
                      schedule(
                        safe(() => {
                          setPhase("exit");
                          schedule(safe(() => run()), 900);
                        }),
                        5200
                      );
                    }),
                    2400
                  );
                }),
                550
              );
            }
          };
          timerRef.current = setTimeout(typeNext, 700);
        }),
        1400
      );
    };

    run();

    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [schedule]);

  const showUrl = phase !== "video";
  const isAnalyzing = phase === "analyzing";
  const showResults = phase === "results";

  return (
    <div className="w-full max-w-2xl mx-auto mt-8">
      {/* Video card */}
      <AnimatePresence>
        {phase === "video" && (
          <motion.div
            key="videocard"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16, scale: 0.97 }}
            transition={{ duration: 0.38, ease: [0.22, 1, 0.36, 1] }}
            className="mb-3 flex items-center gap-3 rounded-xl border border-white/[0.07] bg-[#131313] px-4 py-3"
          >
            <div className="relative w-20 h-12 rounded-lg overflow-hidden shrink-0 bg-gradient-to-br from-[#E84A2F]/25 to-[#0A0A0A]">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-6 h-6 rounded-full bg-white/90 flex items-center justify-center shadow-md">
                  <svg
                    className="w-2.5 h-2.5 text-[#E84A2F] ml-0.5"
                    fill="currentColor"
                    viewBox="0 0 8 10"
                    aria-hidden="true"
                  >
                    <path d="M0 0l8 5-8 5V0z" />
                  </svg>
                </div>
              </div>
              <div className="absolute bottom-1 right-1 bg-black/80 text-white text-[9px] font-mono px-1 rounded">
                {DEMO_VIDEO_DURATION}
              </div>
            </div>
            <div className="min-w-0">
              <p className="text-[13px] text-white/75 font-medium leading-snug line-clamp-1">
                {DEMO_VIDEO_TITLE}
              </p>
              <p className="text-[11px] text-white/25 mt-0.5">YouTube · Long-form video</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Demo search bar */}
      <div
        className={`flex items-center gap-3 rounded-xl border px-4 py-1 transition-all duration-500 ${
          isAnalyzing
            ? "border-[#E84A2F]/40 bg-[#E84A2F]/[0.04] shadow-[0_0_28px_rgba(232,74,47,0.10)]"
            : "border-white/[0.08] bg-[#131313]"
        }`}
      >
        {/* YouTube icon */}
        <svg
          className="w-4 h-4 text-red-500 shrink-0"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
        </svg>

        {/* URL text */}
        <span className="flex-1 py-3.5 text-sm font-mono truncate">
          {!showUrl ? (
            <span className="text-white/20">Paste a YouTube URL...</span>
          ) : (
            <span className="text-white/55">
              {DEMO_URL_TEXT.slice(0, typedChars)}
              {phase === "entering" && (
                <span className="inline-block w-0.5 h-3.5 bg-white/50 ml-0.5 animate-pulse align-middle" />
              )}
            </span>
          )}
        </span>

        {/* Button */}
        <div
          className={`shrink-0 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-300 ${
            isAnalyzing
              ? "bg-[#E84A2F]/15 text-[#E84A2F] border border-[#E84A2F]/25"
              : "bg-[#E84A2F] text-white"
          }`}
        >
          {isAnalyzing ? (
            <span className="flex items-center gap-1.5">
              <motion.span
                animate={{ opacity: [1, 0.4, 1] }}
                transition={{ repeat: Infinity, duration: 1.1 }}
              >
                Analyzing
              </motion.span>
              <span className="flex gap-0.5 items-center">
                {[0, 0.18, 0.36].map((d) => (
                  <motion.span
                    key={d}
                    className="w-1 h-1 rounded-full bg-[#E84A2F] inline-block"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ repeat: Infinity, duration: 1.1, delay: d }}
                  />
                ))}
              </span>
            </span>
          ) : (
            "Find Hooks →"
          )}
        </div>
      </div>

      {/* Waveform (analyzing phase) */}
      <AnimatePresence>
        {isAnalyzing && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.28 }}
            className="overflow-hidden"
          >
            <div className="mt-3 rounded-xl border border-white/[0.06] bg-[#0E0E0E] p-4">
              <p className="text-[10px] text-white/20 font-mono uppercase tracking-widest mb-3">
                Scanning for hook moments...
              </p>
              <WaveformScan active />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hook results */}
      <AnimatePresence>
        {showResults && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="mt-4 space-y-2.5"
          >
            <p className="text-[10px] text-white/20 font-mono uppercase tracking-widest px-1 mb-3">
              5 hooks found · Showing top 3
            </p>
            {DEMO_HOOKS.map((hook, i) => (
              <DemoHookCard key={hook.type} hook={hook} index={i} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Real URL input (interactive) ──────────────────────────────────────────────

interface HeroUrlInputProps {
  onAnalyze: MarketingHomeProps["onAnalyze"];
  light?: boolean;
}

const HeroUrlInput = memo(function HeroUrlInput({
  onAnalyze,
  light = false,
}: HeroUrlInputProps) {
  const [url, setUrl] = useState("");
  const [validating, setValidating] = useState(false);
  const [videoMeta, setVideoMeta] = useState<VideoMeta | null>(null);
  const [error, setError] = useState("");
  const [niche, setNiche] = useState("Generic");

  const handleUrlChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
    setVideoMeta(null);
    setError("");
  }, []);

  const handleValidate = useCallback(async () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    setValidating(true);
    setError("");
    setVideoMeta(null);
    try {
      const result = await api.validateUrl(trimmed);
      if (result.valid && result.video_id && result.title) {
        setVideoMeta({
          video_id: result.video_id,
          title: result.title,
          duration_seconds: result.duration_seconds ?? 0,
        });
      } else {
        setError(result.error ?? "Invalid YouTube URL");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setValidating(false);
    }
  }, [url]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") handleValidate();
    },
    [handleValidate]
  );

  const handleSubmit = useCallback(() => {
    if (!videoMeta) return;
    onAnalyze(url.trim(), niche, "auto", videoMeta);
  }, [url, niche, videoMeta, onAnalyze]);

  const borderBase = light
    ? "border-[#E4E4E7] bg-white focus-within:border-[#E84A2F]/50"
    : "border-white/[0.09] bg-white/[0.04] focus-within:border-[#E84A2F]/40 focus-within:bg-white/[0.06]";
  const textColor = light
    ? "text-[#111] placeholder:text-[#A1A1AA]"
    : "text-white/75 placeholder:text-white/25";
  const microColor = light ? "text-[#A1A1AA]" : "text-white/25";

  return (
    <div className="w-full">
      <div
        className={`flex items-center gap-2 border rounded-xl px-4 py-1 transition-all duration-300 shadow-sm ${borderBase}`}
      >
        <svg
          className="w-5 h-5 text-red-500 shrink-0"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
        </svg>
        <input
          type="text"
          value={url}
          onChange={handleUrlChange}
          onKeyDown={handleKeyDown}
          placeholder="Paste a YouTube URL..."
          className={`flex-1 bg-transparent outline-none py-3.5 text-base ${textColor}`}
          aria-label="YouTube URL"
        />
        <button
          onClick={handleValidate}
          disabled={validating || !url.trim()}
          className="shrink-0 px-5 py-2.5 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] disabled:opacity-40 transition-colors flex items-center gap-2"
        >
          {validating && (
            <svg
              className="w-4 h-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="3"
                strokeDasharray="30 70"
              />
            </svg>
          )}
          {validating ? "Checking…" : "Find My Hooks →"}
        </button>
      </div>

      {!videoMeta && !error && (
        <p className={`text-xs mt-3 text-center ${microColor}`}>
          120 free minutes · No credit card · Results in ~2 min
        </p>
      )}

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-3 text-sm text-red-400 text-center"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {videoMeta && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={`mt-4 p-4 rounded-xl border ${
              light
                ? "bg-white border-[#E4E4E7]"
                : "bg-white/[0.04] border-white/[0.08]"
            }`}
          >
            <p
              className={`text-sm font-medium line-clamp-1 mb-1 ${light ? "text-[#111]" : "text-white/80"}`}
            >
              {videoMeta.title}
            </p>
            <p className={`text-xs mb-4 ${light ? "text-[#71717A]" : "text-white/30"}`}>
              {formatDuration(videoMeta.duration_seconds)} ·{" "}
              ~{(videoMeta.duration_seconds / 60).toFixed(1)} credits
            </p>
            <div className="flex flex-wrap gap-1.5 mb-4">
              {NICHES.map((n) => (
                <button
                  key={n}
                  onClick={() => setNiche(n)}
                  className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
                    niche === n
                      ? "bg-[#E84A2F] text-white border-[#E84A2F]"
                      : light
                        ? "text-[#71717A] border-[#E4E4E7] hover:border-[#D4D4D8]"
                        : "text-white/40 border-white/[0.1] hover:border-white/20"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
            <button
              onClick={handleSubmit}
              className="w-full py-3 rounded-xl bg-[#E84A2F] text-white font-semibold text-sm hover:bg-[#D13F25] transition-colors"
            >
              Start Analyzing →
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

// ── Icon helpers ──────────────────────────────────────────────────────────────

function CheckIcon() {
  return (
    <svg
      className="w-4 h-4 text-[#E84A2F] shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg
      className="w-4 h-4 text-red-400/50 shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  );
}

// ── Pricing card ──────────────────────────────────────────────────────────────

interface PriceCardProps {
  name: string;
  price: string;
  priceINR: string;
  credits: string;
  features: readonly string[];
  highlighted?: boolean;
  cta: string;
}

function PriceCard({
  name,
  price,
  priceINR,
  credits,
  features,
  highlighted,
  cta,
}: PriceCardProps) {
  return (
    <div
      className={`rounded-2xl p-6 flex flex-col gap-4 ${
        highlighted
          ? "bg-[#E84A2F] text-white"
          : "bg-[#141414] border border-white/[0.08]"
      }`}
    >
      <div>
        <div
          className={`text-xs font-semibold uppercase tracking-wider mb-1 ${
            highlighted ? "text-white/70" : "text-white/30"
          }`}
        >
          {name}
        </div>
        <div
          className={`text-3xl font-bold font-mono ${
            highlighted ? "text-white" : "text-white/90"
          }`}
        >
          {price}
        </div>
        <div className={`text-sm ${highlighted ? "text-white/70" : "text-white/30"}`}>
          {priceINR} · {credits}
        </div>
      </div>
      <ul className="space-y-2.5 flex-1">
        {features.map((f) => (
          <li
            key={f}
            className={`flex items-center gap-2.5 text-sm ${
              highlighted ? "text-white/90" : "text-white/50"
            }`}
          >
            <svg
              className={`w-4 h-4 shrink-0 ${highlighted ? "text-white" : "text-[#E84A2F]"}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M5 13l4 4L19 7"
              />
            </svg>
            {f}
          </li>
        ))}
      </ul>
      <button
        className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-colors ${
          highlighted
            ? "bg-white text-[#E84A2F] hover:bg-white/90"
            : "bg-[#E84A2F] text-white hover:bg-[#D13F25]"
        }`}
      >
        {cta}
      </button>
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

export const MarketingHome = memo(function MarketingHome({
  onAnalyze,
}: MarketingHomeProps) {
  return (
    <div>
      <style>{`
        @keyframes mkticker { from { transform: translateX(0) } to { transform: translateX(-50%) } }
        .mk-ticker { animation: mkticker 30s linear infinite; display: flex; width: max-content; }
      `}</style>

      {/* ── 1. HERO ────────────────────────────────────────────────────────── */}
      <section className="relative bg-[#0A0A0A] min-h-screen flex flex-col items-center justify-center overflow-hidden px-6 pt-24 pb-16">
        {/* Grid background */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)
            `,
            backgroundSize: "64px 64px",
          }}
          aria-hidden="true"
        />
        {/* Top orange glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(232,74,47,0.07), transparent)",
          }}
          aria-hidden="true"
        />

        <div className="relative w-full max-w-3xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#E84A2F]/[0.1] border border-[#E84A2F]/20 text-[#E84A2F] text-xs font-semibold mb-8"
          >
            <span
              className="w-1.5 h-1.5 rounded-full bg-[#E84A2F] animate-pulse"
              aria-hidden="true"
            />
            AI Hook Detection for YouTube Shorts
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="text-[clamp(44px,7.5vw,100px)] font-extrabold text-white leading-[1.0] tracking-[-0.04em] mb-6 font-[family-name:--font-display]"
          >
            Find the hook.
            <br />
            <span className="text-[#E84A2F]">Stop the scroll.</span>
          </motion.h1>

          {/* Sub */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.22 }}
            className="text-white/40 text-lg leading-relaxed mb-10 max-w-xl mx-auto"
          >
            Paste any YouTube URL. HookCut finds the 5 moments most likely to go viral —
            scored, explained, and ready to post as Shorts.
          </motion.p>

          {/* Real input */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.32 }}
            className="max-w-2xl mx-auto"
          >
            <HeroUrlInput onAnalyze={onAnalyze} light={false} />
          </motion.div>

          {/* Separator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="flex items-center gap-4 my-10 max-w-2xl mx-auto"
          >
            <div className="h-px flex-1 bg-white/[0.05]" />
            <span className="text-white/20 text-[10px] font-mono uppercase tracking-widest whitespace-nowrap">
              or watch it work
            </span>
            <div className="h-px flex-1 bg-white/[0.05]" />
          </motion.div>

          {/* Demo */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.68 }}
          >
            <HeroDemo />
          </motion.div>
        </div>

        {/* Scroll cue */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2.2, duration: 0.8 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
          aria-hidden="true"
        >
          <motion.div
            animate={{ y: [0, 7, 0] }}
            transition={{ repeat: Infinity, duration: 2.2, ease: "easeInOut" }}
            className="w-5 h-8 rounded-full border border-white/[0.1] flex items-start justify-center pt-1.5"
          >
            <div className="w-1 h-2 rounded-full bg-white/25" />
          </motion.div>
        </motion.div>
      </section>

      {/* ── 2. MARQUEE ─────────────────────────────────────────────────────── */}
      <div className="bg-[#111] border-y border-white/[0.05] py-3.5 overflow-hidden">
        <div className="mk-ticker gap-14 whitespace-nowrap">
          {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
            <span
              key={i}
              className="text-white/30 text-xs font-medium shrink-0 tracking-wide"
            >
              {item}
              <span className="mx-8 text-white/[0.1]" aria-hidden="true">·</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── 3. STATEMENT ───────────────────────────────────────────────────── */}
      <section className="bg-[#FAFAF8] py-28 px-6 overflow-hidden">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-8">
            The problem
          </p>
          <div className="flex flex-col leading-none">
            <span
              className="text-[#111] font-extrabold tracking-[-0.04em] font-[family-name:--font-display]"
              style={{ fontSize: "clamp(48px,7vw,108px)", lineHeight: 0.95 }}
            >
              The first
            </span>
            <span
              className="text-[#E84A2F] font-extrabold tracking-[-0.04em] font-[family-name:--font-display]"
              style={{ fontSize: "clamp(80px,13vw,192px)", lineHeight: 0.88 }}
            >
              2 secs
            </span>
            <span
              className="text-[#111] font-extrabold tracking-[-0.04em] font-[family-name:--font-display]"
              style={{ fontSize: "clamp(48px,7vw,108px)", lineHeight: 0.95 }}
            >
              decide everything.
            </span>
          </div>
          <p className="mt-12 text-[#71717A] text-lg leading-relaxed max-w-lg">
            Most viewers scroll past a video in under 2 seconds. The difference between 10
            views and 10 million isn&apos;t production quality — it&apos;s the first line.
            HookCut finds that line in your video.
          </p>
        </div>
      </section>

      {/* ── 4. HOW IT WORKS ────────────────────────────────────────────────── */}
      <section className="bg-[#F5F5F3] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            How It Works
          </p>
          <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-[#111] tracking-[-0.03em] mb-16 font-[family-name:--font-display]">
            Three steps.
            <br />
            One viral Short.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {(
              [
                {
                  n: "01",
                  title: "Paste your YouTube URL",
                  desc: "Any video, any length, any language. Podcasts, tutorials, vlogs — all supported.",
                },
                {
                  n: "02",
                  title: "AI surfaces the hook moments",
                  desc: "HookCut scores every moment in your video and surfaces the 5 most likely to go viral — each one explained.",
                },
                {
                  n: "03",
                  title: "Download your Shorts",
                  desc: "Ready-to-post 9:16 clips with captions. No editing software. No guesswork.",
                },
              ] as const
            ).map((step) => (
              <div key={step.n} className="flex flex-col gap-4">
                <span className="text-[56px] font-extrabold text-[#E84A2F] font-mono leading-none tracking-[-0.05em]">
                  {step.n}
                </span>
                <div className="h-px w-8 bg-[#E84A2F]/30" />
                <h3 className="text-[#111] font-bold text-lg">{step.title}</h3>
                <p className="text-[#71717A] text-sm leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 5. HOOK SHOWCASE (offset layout) ───────────────────────────────── */}
      <section className="bg-[#FAFAF8] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            Hook Intelligence
          </p>
          <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-[#111] tracking-[-0.03em] mb-4 font-[family-name:--font-display]">
            Every moment scored.
            <br />
            Only the best ones ship.
          </h2>
          <p className="text-[#71717A] text-base mb-14 max-w-lg">
            HookCut intelligently rejects filler, greetings, and sponsor segments. What
            remains: the moments most likely to stop a scroll.
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 lg:items-start">
            {DEMO_HOOKS.map((hook, i) => {
              const offsets = ["lg:mt-0", "lg:mt-10", "lg:mt-5"];
              const circumference = 2 * Math.PI * 28;
              const strokeOffset = circumference - (hook.score / 10) * circumference;
              return (
                <div
                  key={hook.type}
                  className={`rounded-2xl border border-[#E4E4E7] bg-white p-6 flex flex-col gap-4 shadow-sm ${offsets[i]}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="relative w-16 h-16 shrink-0">
                      <svg
                        viewBox="0 0 64 64"
                        className="w-full h-full -rotate-90"
                        aria-hidden="true"
                      >
                        <circle
                          cx="32"
                          cy="32"
                          r="28"
                          fill="none"
                          stroke="#F4F4F5"
                          strokeWidth="4"
                        />
                        <circle
                          cx="32"
                          cy="32"
                          r="28"
                          fill="none"
                          stroke={hook.color}
                          strokeWidth="4"
                          strokeLinecap="round"
                          strokeDasharray={circumference}
                          strokeDashoffset={strokeOffset}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="font-mono font-bold text-[#111] text-base">
                          {hook.score}
                        </span>
                      </div>
                    </div>
                    <div>
                      <span
                        className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full"
                        style={{
                          color: hook.color,
                          background: `${hook.color}18`,
                          border: `1px solid ${hook.color}30`,
                        }}
                      >
                        {hook.type}
                      </span>
                      <p className="text-[11px] text-[#A1A1AA] font-mono mt-2">
                        {hook.timestamp}
                      </p>
                    </div>
                  </div>
                  <p className="text-[13px] text-[#0A0A0A]/60 leading-relaxed">{hook.text}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── 6. COMPARISON ──────────────────────────────────────────────────── */}
      <section className="bg-[#F5F5F3] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            Why HookCut
          </p>
          <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-[#111] tracking-[-0.03em] mb-12 font-[family-name:--font-display]">
            What nobody else does.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-14">
            <div className="rounded-2xl bg-[#EBEBEB] p-6">
              <p className="text-[#71717A] text-xs font-semibold uppercase tracking-wider mb-5">
                Other AI Clippers
              </p>
              <ul className="space-y-3">
                {(
                  [
                    "Cut at every sentence, good or bad",
                    "Include greeting clips and filler",
                    "Give you 40 clips to sort through",
                    "No explanation of why clips were chosen",
                    "$29–$79/month, billed in USD",
                  ] as const
                ).map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm text-[#71717A]">
                    <XIcon />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl bg-white border border-[#E84A2F]/15 p-6 shadow-sm">
              <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-wider mb-5">
                HookCut
              </p>
              <ul className="space-y-3">
                {(
                  [
                    "Scores every moment, only ships the best",
                    "Actively rejects greetings and sponsors",
                    "Surfaces 5 high-quality hook segments",
                    "Explains why each moment is scroll-stopping",
                    "₹499/month with UPI support",
                  ] as const
                ).map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm text-[#111]/80">
                    <CheckIcon />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="overflow-x-auto rounded-2xl border border-[#E4E4E7] bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E4E4E7]">
                  <th className="text-left p-4 text-[#71717A] font-medium w-44">Feature</th>
                  <th className="p-4 text-[#E84A2F] font-bold text-center">HookCut</th>
                  <th className="p-4 text-[#71717A] font-medium text-center">OpusClip</th>
                  <th className="p-4 text-[#71717A] font-medium text-center">Klap</th>
                  <th className="p-4 text-[#71717A] font-medium text-center">Vizard</th>
                </tr>
              </thead>
              <tbody>
                {(
                  [
                    ["Hook Score (0–10)", "✓", "✗", "✗", "✗"],
                    ["Explains why each clip was chosen", "✓", "✗", "✗", "✗"],
                    ["Rejects filler clips automatically", "✓", "✗", "✗", "✗"],
                    ["Price / month (USD)", "$7", "$29+", "$17+", "$19+"],
                    ["India pricing (INR + UPI)", "✓", "✗", "✗", "✗"],
                    ["Cancel anytime", "✓", "✓", "✓", "✓"],
                  ] as const
                ).map(([feature, hookcut, opus, klap, vizard], i) => (
                  <tr key={feature} className={i % 2 === 0 ? "bg-white" : "bg-[#FAFAF8]"}>
                    <td className="p-4 text-[#0A0A0A]/70 font-medium">{feature}</td>
                    <td className="p-4 text-center font-semibold text-[#E84A2F]">{hookcut}</td>
                    <td className="p-4 text-center text-[#71717A]">{opus}</td>
                    <td className="p-4 text-center text-[#71717A]">{klap}</td>
                    <td className="p-4 text-center text-[#71717A]">{vizard}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── 7. TESTIMONIALS ────────────────────────────────────────────────── */}
      <section className="bg-[#FAFAF8] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            Creators who switched
          </p>
          <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-[#111] tracking-[-0.03em] mb-14 font-[family-name:--font-display]">
            Real results.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:items-start">
            {(
              [
                {
                  quote:
                    "My Shorts went from 800 to 14,000 views after using HookCut's hook scoring.",
                  name: "@techcreator_in",
                  sub: "47K subscribers",
                  initials: "TC",
                  color: "bg-blue-600",
                  offset: "",
                },
                {
                  quote:
                    "I found the exact moment in my 45-min podcast that got 2M views as a Short.",
                  name: "@financewithravi",
                  sub: "128K subscribers",
                  initials: "FR",
                  color: "bg-emerald-600",
                  offset: "md:mt-8",
                },
                {
                  quote: "Saved me 3 hours of editing. First Short hit 400K views within a week.",
                  name: "@learningwithpriya",
                  sub: "22K subscribers",
                  initials: "LP",
                  color: "bg-violet-600",
                  offset: "md:mt-4",
                },
              ] as const
            ).map((t) => (
              <div
                key={t.name}
                className={`bg-white border border-[#E4E4E7] rounded-2xl p-6 shadow-sm ${t.offset}`}
              >
                <div className="flex gap-0.5 mb-4" aria-label="5 stars">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <svg
                      key={s}
                      className="w-4 h-4 text-amber-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                      aria-hidden="true"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-[#0A0A0A]/75 text-[15px] leading-relaxed mb-5">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="flex items-center gap-3">
                  <div
                    className={`w-8 h-8 rounded-full ${t.color} flex items-center justify-center text-white text-xs font-bold shrink-0`}
                    aria-hidden="true"
                  >
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-[#111] text-sm font-semibold">{t.name}</p>
                    <p className="text-[#A1A1AA] text-xs">{t.sub}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 8. INDIA ───────────────────────────────────────────────────────── */}
      <section className="bg-[#F5F5F3] py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-[clamp(24px,3.5vw,44px)] font-extrabold text-[#111] mb-4 tracking-[-0.03em] font-[family-name:--font-display]">
            Built for creators across India.
          </h2>
          <p className="text-[#71717A] text-base leading-relaxed mb-8">
            Pay in rupees. Analyze Hinglish content. ₹499/month — no dollar conversion
            surprises.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {(
              [
                "🇮🇳  ₹499/month",
                "UPI accepted",
                "12+ Indian languages",
                "Hinglish supported",
              ] as const
            ).map((pill) => (
              <span
                key={pill}
                className="px-4 py-2 rounded-full bg-white border border-[#E4E4E7] text-[#111] text-sm font-medium shadow-sm"
              >
                {pill}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── 9. PRICING ─────────────────────────────────────────────────────── */}
      <section className="bg-[#0A0A0A] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
              Pricing
            </p>
            <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-white tracking-[-0.03em] font-[family-name:--font-display]">
              Simple, honest pricing.
            </h2>
            <p className="text-white/30 text-sm mt-3">
              No billing surprises. Credits refunded on analysis failures.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <PriceCard
              name="Free"
              price="$0"
              priceINR="₹0"
              credits="120 min included"
              features={["5 hooks per video", "3 Shorts per batch", "Watermarked clips"]}
              cta="Start Free"
            />
            <PriceCard
              name="Lite"
              price="$7"
              priceINR="₹499/mo"
              credits="500 min/month"
              features={[
                "5 hooks per video",
                "10 Shorts per batch",
                "No watermark",
                "Priority queue",
              ]}
              highlighted
              cta="Start Analyzing →"
            />
            <PriceCard
              name="Pro"
              price="$19"
              priceINR="₹1,499/mo"
              credits="2,000 min/month"
              features={[
                "5 hooks per video",
                "Unlimited Shorts",
                "API access",
                "Custom captions",
              ]}
              cta="Go Pro"
            />
          </div>
          <p className="text-center mt-8">
            <Link href="/pricing" className="text-[#E84A2F] text-sm font-medium hover:underline">
              See full pricing →
            </Link>
          </p>
        </div>
      </section>

      {/* ── 10. FINAL CTA ──────────────────────────────────────────────────── */}
      <section className="bg-[#111] border-t border-white/[0.05] py-24 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-[clamp(32px,5vw,68px)] font-extrabold text-white mb-3 tracking-[-0.04em] leading-[1.05] font-[family-name:--font-display]">
            Your next viral Short
            <br />
            is already in your video.
          </h2>
          <p className="text-white/30 text-base mb-10">Find it in under 2 minutes.</p>
          <HeroUrlInput onAnalyze={onAnalyze} light={false} />
        </div>
      </section>
    </div>
  );
});

export default MarketingHome;
