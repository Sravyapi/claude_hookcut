"use client";

import { memo, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { HeroHookPreview } from "./hero-hook-preview";
import { HookTimeline, type TimelineHook } from "./hook-timeline";
import type { VideoMeta } from "../lib/types";
import { api } from "../lib/api";
import { NICHES } from "../lib/constants";
import { formatDuration } from "../lib/utils";

// ── Types ──────────────────────────────────────────────────────────────────

interface MarketingHomeProps {
  onAnalyze: (url: string, niche: string, language: string, meta: VideoMeta) => void;
}

// ── Demo data ──────────────────────────────────────────────────────────────

const DEMO_TIMELINE_HOOKS: TimelineHook[] = [
  { id: "d1", start_time: "0:14", attention_score: 9.2, rank: 1 },
  { id: "d2", start_time: "1:32", attention_score: 8.5, rank: 2 },
  { id: "d3", start_time: "3:07", attention_score: 7.8, rank: 3 },
  { id: "d4", start_time: "5:41", attention_score: 8.1, rank: 4 },
  { id: "d5", start_time: "8:23", attention_score: 7.3, rank: 5 },
];

const DEMO_HOOKS = [
  {
    score: 9.2,
    grade: "Exceptional",
    gradeColor: "#16A34A",
    type: "CURIOSITY GAP",
    text: "Nobody talks about this YouTube trick that tripled my views overnight...",
    typeColor: "bg-orange-50 text-orange-700 border-orange-200",
  },
  {
    score: 8.5,
    grade: "Exceptional",
    gradeColor: "#16A34A",
    type: "FEAR-BASED",
    text: "I tested 10 AI tools and what happened next shocked my entire team...",
    typeColor: "bg-red-50 text-red-700 border-red-200",
  },
  {
    score: 7.1,
    grade: "High Impact",
    gradeColor: "#E84A2F",
    type: "CONTRARIAN",
    text: "Everyone is wrong about what makes a Short go viral in 2025...",
    typeColor: "bg-amber-50 text-amber-700 border-amber-200",
  },
] as const;

const TICKER_ITEMS = [
  "10,000+ hooks analyzed",
  "Used by 2,000+ creators",
  "4.8★ from creators",
  "Built for Indian creators",
  "#1 hook finder for YouTube",
  "120 free minutes on signup",
  "Results in ~2 minutes",
  "No credit card required",
];

// ── Sub-components ─────────────────────────────────────────────────────────

function DemoHookCard({ hook }: { hook: typeof DEMO_HOOKS[number] }) {
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (hook.score / 10) * circumference;
  return (
    <div className="bg-white rounded-2xl border border-[#E4E4E7] p-5 flex flex-col items-center gap-3 shadow-sm">
      <div className="relative w-20 h-20">
        <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90" aria-hidden="true">
          <circle cx="40" cy="40" r="36" fill="none" stroke="#F4F4F5" strokeWidth="5" />
          <circle
            cx="40" cy="40" r="36" fill="none"
            stroke={hook.gradeColor} strokeWidth="5" strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold text-[#0A0A0A] font-mono">{hook.score.toFixed(1)}</span>
          <span className="text-[9px] text-[#A1A1AA] uppercase tracking-wide">score</span>
        </div>
      </div>
      <span className="text-xs font-semibold" style={{ color: hook.gradeColor }}>{hook.grade}</span>
      <span className={`text-[11px] px-2.5 py-0.5 rounded-full border font-semibold ${hook.typeColor}`}>
        {hook.type}
      </span>
      <p className="text-[13px] text-[#0A0A0A]/70 text-center leading-relaxed line-clamp-3">{hook.text}</p>
    </div>
  );
}

function CheckIcon({ className = "" }: { className?: string }) {
  return (
    <svg className={`w-4 h-4 shrink-0 ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
    </svg>
  );
}

function XIcon({ className = "" }: { className?: string }) {
  return (
    <svg className={`w-4 h-4 shrink-0 ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

interface PriceCardProps {
  name: string;
  price: string;
  priceINR: string;
  credits: string;
  features: readonly string[];
  highlighted?: boolean;
  cta: string;
}

function PriceCard({ name, price, priceINR, credits, features, highlighted, cta }: PriceCardProps) {
  return (
    <div
      className={`rounded-2xl p-6 flex flex-col gap-4 ${
        highlighted
          ? "bg-[#E84A2F] text-white shadow-lg ring-2 ring-[#E84A2F]"
          : "bg-white border border-[#E4E4E7]"
      }`}
    >
      <div>
        <div className={`text-xs font-semibold uppercase tracking-wider mb-1 ${highlighted ? "text-white/70" : "text-[#71717A]"}`}>
          {name}
        </div>
        <div className={`text-3xl font-bold font-mono ${highlighted ? "text-white" : "text-[#0A0A0A]"}`}>
          {price}
        </div>
        <div className={`text-sm ${highlighted ? "text-white/70" : "text-[#71717A]"}`}>
          {priceINR} · {credits}
        </div>
      </div>
      <ul className="space-y-2 flex-1">
        {features.map((f) => (
          <li key={f} className={`flex items-center gap-2 text-sm ${highlighted ? "text-white/90" : "text-[#0A0A0A]/70"}`}>
            <CheckIcon className={highlighted ? "text-white" : "text-[#E84A2F]"} />
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

// ── Hero URL Input ─────────────────────────────────────────────────────────

interface HeroUrlInputProps {
  onAnalyze: MarketingHomeProps["onAnalyze"];
  light?: boolean;
}

const HeroUrlInput = memo(function HeroUrlInput({ onAnalyze, light = true }: HeroUrlInputProps) {
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

  const handleNiche = useCallback((n: string) => setNiche(n), []);

  const handleSubmit = useCallback(() => {
    if (!videoMeta) return;
    onAnalyze(url.trim(), niche, "auto", videoMeta);
  }, [url, niche, videoMeta, onAnalyze]);

  const inputBg = light ? "bg-white border-[#E4E4E7] focus-within:border-[#E84A2F]/50" : "bg-white/10 border-white/20 focus-within:border-white/40";
  const textColor = light ? "text-[#0A0A0A] placeholder:text-[#A1A1AA]" : "text-white placeholder:text-white/40";
  const microColor = light ? "text-[#A1A1AA]" : "text-white/40";

  return (
    <div className="w-full">
      <div className={`flex items-center gap-2 border rounded-xl px-4 py-1 shadow-sm transition-all ${inputBg}`}>
        <svg className="w-5 h-5 text-red-500 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
        </svg>
        <input
          type="text"
          value={url}
          onChange={handleUrlChange}
          onKeyDown={handleKeyDown}
          placeholder="https://youtube.com/watch?v=..."
          className={`flex-1 bg-transparent outline-none py-3.5 text-base ${textColor}`}
          aria-label="YouTube URL"
        />
        <button
          onClick={handleValidate}
          disabled={validating || !url.trim()}
          className="shrink-0 px-5 py-2.5 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] disabled:opacity-40 transition-colors flex items-center gap-2"
        >
          {validating && (
            <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="30 70" />
            </svg>
          )}
          {validating ? "Checking…" : "Find My Hooks →"}
        </button>
      </div>

      {!videoMeta && !error && (
        <p className={`text-xs mt-3 text-center ${microColor}`}>
          120 free minutes · No credit card · Results in ~2 minutes
        </p>
      )}

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="mt-3 text-sm text-red-500 text-center"
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
            exit={{ opacity: 0, y: -4 }}
            className="mt-4 p-4 bg-white border border-[#E4E4E7] rounded-xl"
          >
            <p className="text-sm text-[#0A0A0A] font-medium line-clamp-1 mb-0.5">{videoMeta.title}</p>
            <p className="text-xs text-[#71717A] mb-4">
              {formatDuration(videoMeta.duration_seconds)} · ~{(videoMeta.duration_seconds / 60).toFixed(1)} credits
            </p>
            <div className="flex flex-wrap gap-1.5 mb-4">
              {NICHES.map((n) => (
                <button
                  key={n}
                  onClick={() => handleNiche(n)}
                  className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
                    niche === n
                      ? "bg-[#E84A2F] text-white border-[#E84A2F]"
                      : "bg-white text-[#71717A] border-[#E4E4E7] hover:border-[#D4D4D8]"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
            <button
              onClick={handleSubmit}
              className="w-full py-3 rounded-xl bg-[#E84A2F] text-white font-semibold text-sm hover:bg-[#D13F25] transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Start Analyzing →
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

// ── Main Component ─────────────────────────────────────────────────────────

export const MarketingHome = memo(function MarketingHome({ onAnalyze }: MarketingHomeProps) {
  return (
    <div className="bg-[#FAFAF8]">

      {/* Ticker keyframe */}
      <style>{`
        @keyframes mkticker { from { transform: translateX(0) } to { transform: translateX(-50%) } }
        .mk-ticker { animation: mkticker 24s linear infinite; display: flex; width: max-content; }
      `}</style>

      {/* ── Section 1: Hero ──────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 pt-32 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-[60%_40%] gap-12 items-center">

          {/* Left: Copy + Input */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#E84A2F]/8 border border-[#E84A2F]/15 text-[#E84A2F] text-xs font-semibold mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-[#E84A2F] animate-pulse" aria-hidden="true" />
              Hook Detection for YouTube Shorts
            </div>

            <h1 className="text-[56px] sm:text-[64px] font-extrabold text-[#0A0A0A] leading-[1.05] tracking-[-0.04em] mb-5 font-[family-name:--font-display]">
              Find the hook.<br />
              <span className="text-[#E84A2F]">Stop the scroll.</span>
            </h1>

            <p className="text-[#71717A] text-lg leading-relaxed mb-8 max-w-xl">
              Paste any YouTube URL. HookCut identifies the moments most likely to go viral — scored, explained, and ready to post as Shorts.
            </p>

            <HeroUrlInput onAnalyze={onAnalyze} />
          </div>

          {/* Right: Static visual */}
          <div className="hidden lg:flex flex-col items-center justify-center">
            <HeroHookPreview />
          </div>
        </div>
      </section>

      {/* ── Section 2: Social Proof Ticker ──────────────────────────────── */}
      <div className="bg-[#0A0A0A] py-4 overflow-hidden">
        <div className="mk-ticker gap-14 whitespace-nowrap">
          {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
            <span key={i} className="text-white/50 text-sm font-medium shrink-0">
              {item}
              <span className="mx-8 text-white/20" aria-hidden="true">·</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── Section 3: How It Works ──────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 py-24">
        <div className="text-center mb-14">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">How It Works</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-[#0A0A0A] tracking-tight font-[family-name:--font-display]">
            Three steps. One viral Short.
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
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
                desc: "HookCut intelligently finds the moments most likely to stop a scroll — each one scored and explained.",
              },
              {
                n: "03",
                title: "Download your Shorts",
                desc: "Ready-to-post 9:16 clips with captions, trimmed to hook-length. No editing software needed.",
              },
            ] as const
          ).map((step) => (
            <div key={step.n} className="flex flex-col gap-3">
              <span className="text-5xl font-extrabold text-[#E84A2F] font-mono leading-none">{step.n}</span>
              <h3 className="text-[#0A0A0A] font-semibold text-[18px] leading-snug">{step.title}</h3>
              <p className="text-[#71717A] text-sm leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Section 4: The Problem ───────────────────────────────────────── */}
      <section className="bg-white border-y border-[#E4E4E7] py-24">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-[#0A0A0A] mb-4 tracking-tight font-[family-name:--font-display]">
              Most viewers decide to scroll in the first 2 seconds.
            </h2>
            <p className="text-[#71717A] text-base leading-relaxed max-w-2xl mx-auto">
              The difference between a viral Short and a dead one isn&apos;t the content — it&apos;s the hook. HookCut analyzes your video and identifies the moments most likely to trigger curiosity, emotion, and tension.
            </p>
          </div>
          <div className="bg-[#111111] rounded-2xl p-6 border border-[#222222]">
            <HookTimeline
              hooks={DEMO_TIMELINE_HOOKS}
              durationSeconds={600}
              activeHookId={null}
            />
            <p className="text-center text-xs text-white/30 mt-4 font-mono">
              5 hooks found in this video. Scroll-stopping moments highlighted.
            </p>
          </div>
        </div>
      </section>

      {/* ── Section 5: Example Hooks ─────────────────────────────────────── */}
      <section className="bg-[#F4F4F5] py-24">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-[#0A0A0A] mb-3 tracking-tight font-[family-name:--font-display]">
              Every hook gets a score. Only the best ones ship.
            </h2>
            <p className="text-[#71717A] text-sm">
              HookCut intelligently surfaces the moments most likely to stop a scroll.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {DEMO_HOOKS.map((hook) => (
              <DemoHookCard key={hook.type} hook={hook} />
            ))}
          </div>
          <p className="text-center text-xs text-[#A1A1AA] mt-8">
            Each score reflects scroll-stopping potential. Only hooks above the threshold make the cut.
          </p>
        </div>
      </section>

      {/* ── Section 6: Hook Score Feature Block ─────────────────────────── */}
      <section className="bg-white border-y border-[#E4E4E7] py-24">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">Hook Score Engine</p>
              <h2 className="text-3xl font-bold text-[#0A0A0A] mb-4 tracking-tight font-[family-name:--font-display]">
                The feature nobody else has.
              </h2>
              <p className="text-[#71717A] text-base leading-relaxed mb-6">
                HookCut intelligently surfaces the moments in your video that are most likely to stop a scroll. Each one gets a score based on engagement potential — so you know exactly which clips are worth posting.
              </p>
              <ul className="space-y-3">
                {(
                  [
                    "Every moment scored, not just clipped",
                    "Explains why each clip was chosen",
                    "Automatically rejects filler segments",
                    "Works for any niche or language",
                  ] as const
                ).map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm text-[#0A0A0A]/80">
                    <div className="w-5 h-5 rounded-full bg-[#E84A2F]/10 flex items-center justify-center shrink-0">
                      <CheckIcon className="w-3 h-3 text-[#E84A2F]" />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex justify-center">
              <div className="w-full max-w-[260px]">
                <DemoHookCard hook={DEMO_HOOKS[0]} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 7: What Nobody Else Does ────────────────────────────── */}
      <section className="bg-[#F4F4F5] py-24">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-[#0A0A0A] text-center mb-12 tracking-tight font-[family-name:--font-display]">
            What makes HookCut different.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-[#E8E8E8]/60 rounded-2xl p-6">
              <p className="text-[#71717A] text-xs font-semibold uppercase tracking-wider mb-5">Other AI Clippers</p>
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
                    <XIcon className="text-red-400" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-white border border-[#E84A2F]/20 rounded-2xl p-6 shadow-sm">
              <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-wider mb-5">HookCut</p>
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
                  <li key={item} className="flex items-center gap-3 text-sm text-[#0A0A0A]/80">
                    <CheckIcon className="text-[#E84A2F]" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 8: Creator Testimonials ─────────────────────────────── */}
      <section className="bg-white py-24">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-[#0A0A0A] mb-3 tracking-tight font-[family-name:--font-display]">
              Creators who switched.
            </h2>
            <p className="text-[#71717A] text-sm">Real results from real channels.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {(
              [
                {
                  quote: "My Shorts went from 800 to 14,000 views after using HookCut's hook scoring.",
                  name: "@techcreator_in",
                  sub: "47K subscribers",
                  initials: "TC",
                  color: "bg-blue-500",
                },
                {
                  quote: "I found the exact moment in my 45-minute podcast that got 2M views as a Short.",
                  name: "@financewithravi",
                  sub: "128K subscribers",
                  initials: "FR",
                  color: "bg-emerald-500",
                },
                {
                  quote: "Saved me 3 hours of editing. First Short hit 400K views within a week.",
                  name: "@learningwithpriya",
                  sub: "22K subscribers",
                  initials: "LP",
                  color: "bg-violet-500",
                },
              ] as const
            ).map((t) => (
              <div key={t.name} className="bg-[#FAFAF8] border border-[#E4E4E7] rounded-2xl p-6">
                <div className="flex gap-0.5 mb-4" aria-label="5 stars">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <svg key={s} className="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-[#0A0A0A]/80 text-sm leading-relaxed mb-4">&ldquo;{t.quote}&rdquo;</p>
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full ${t.color} flex items-center justify-center text-white text-xs font-bold shrink-0`} aria-hidden="true">
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-[#0A0A0A] text-sm font-semibold">{t.name}</p>
                    <p className="text-[#A1A1AA] text-xs">{t.sub}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section 9: Comparison Table ──────────────────────────────────── */}
      <section className="bg-[#F4F4F5] py-24">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-[#0A0A0A] text-center mb-12 tracking-tight font-[family-name:--font-display]">
            How HookCut stacks up.
          </h2>
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
                    ["Languages supported", "12+", "20+", "8+", "15+"],
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

      {/* ── Section 10: India Section ─────────────────────────────────────── */}
      <section className="bg-white py-20">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-[#0A0A0A] mb-4 tracking-tight font-[family-name:--font-display]">
            Built for creators across India.
          </h2>
          <p className="text-[#71717A] text-base leading-relaxed mb-8">
            Pay in rupees. Analyze Hinglish content. ₹499/month — no dollar conversion surprises.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {(["🇮🇳  ₹499/month", "UPI accepted", "12+ Indian languages", "Hinglish supported"] as const).map((pill) => (
              <span key={pill} className="px-4 py-2 rounded-full bg-[#F4F4F5] border border-[#E4E4E7] text-[#0A0A0A] text-sm font-medium">
                {pill}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section 11: Pricing Preview ──────────────────────────────────── */}
      <section className="bg-[#F4F4F5] py-24">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-[#0A0A0A] mb-3 tracking-tight font-[family-name:--font-display]">
              Simple, honest pricing.
            </h2>
            <p className="text-[#71717A] text-sm">No billing surprises. Credits refunded on analysis failures.</p>
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
              features={["5 hooks per video", "10 Shorts per batch", "No watermark", "Priority queue"]}
              highlighted
              cta="Start Analyzing →"
            />
            <PriceCard
              name="Pro"
              price="$19"
              priceINR="₹1,499/mo"
              credits="2,000 min/month"
              features={["5 hooks per video", "Unlimited Shorts", "API access", "Custom captions"]}
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

      {/* ── Section 12: Final CTA ─────────────────────────────────────────── */}
      <section className="bg-[#0A0A0A] py-24">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-4xl sm:text-5xl font-extrabold text-white mb-3 tracking-tight leading-[1.1] font-[family-name:--font-display]">
            Your next viral Short is already in your video.
          </h2>
          <p className="text-white/40 text-base mb-10">Find it in under 2 minutes.</p>
          <HeroUrlInput onAnalyze={onAnalyze} light={false} />
        </div>
      </section>

    </div>
  );
});

export default MarketingHome;
