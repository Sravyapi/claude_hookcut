"use client";

import { memo } from "react";
import { motion } from "framer-motion";

const MOCK_HOOK = {
  score: 8.7,
  type: "CURIOSITY GAP",
  funnel: "TOFU",
  text: "This one decision changed everything about how I make videos...",
  startTime: "0:43",
  endTime: "1:18",
} as const;

const MOCK_SHORT = {
  caption: "I'm NOT joking about this...",
  views: "2.1M views",
} as const;

/** Score ring — simplified, no Framer Motion needed for static display */
function ScoreRing({ score }: { score: number }) {
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 10) * circumference;

  return (
    <div className="relative w-[80px] h-[80px]">
      <svg viewBox="0 0 72 72" className="w-full h-full -rotate-90" aria-hidden="true">
        <circle cx="36" cy="36" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" />
        <circle
          cx="36"
          cy="36"
          r={radius}
          fill="none"
          stroke="#E84A2F"
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ filter: "drop-shadow(0 0 8px rgba(232,74,47,0.5))" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-white font-mono leading-none">{score.toFixed(1)}</span>
        <span className="text-[9px] text-white/30 uppercase tracking-wider mt-0.5">score</span>
      </div>
    </div>
  );
}

/** Short preview card — mimics a 9:16 phone screen */
function ShortPreviewCard() {
  return (
    <div
      className="w-[140px] aspect-[9/16] bg-[#1A1A1A] rounded-2xl overflow-hidden border border-white/[0.08] shadow-xl shadow-black/40 relative flex-shrink-0"
      aria-hidden="true"
    >
      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/80" />

      {/* Mock thumbnail bars */}
      <div className="absolute inset-0 flex flex-col justify-end p-3">
        <div className="space-y-1 mb-3">
          <div className="h-1.5 bg-white/20 rounded-full w-4/5" />
          <div className="h-1.5 bg-white/15 rounded-full w-3/5" />
        </div>
        {/* Caption overlay */}
        <div className="bg-[--color-primary] px-2 py-1 rounded-lg text-white text-[10px] font-bold text-center leading-tight">
          {MOCK_SHORT.caption}
        </div>
        <div className="mt-2 flex items-center justify-between">
          <span className="text-[9px] text-white/40">{MOCK_SHORT.views}</span>
          <div className="w-4 h-4 rounded-full bg-white/10 flex items-center justify-center">
            <div className="w-0 h-0 border-l-[5px] border-l-white/60 border-y-[3px] border-y-transparent ml-0.5" />
          </div>
        </div>
      </div>

      {/* Notch */}
      <div className="absolute top-2 left-1/2 -translate-x-1/2 w-10 h-1 bg-white/10 rounded-full" />
    </div>
  );
}

/** Hook score card — static preview of the product hook card */
function HookScoreCard() {
  return (
    <div
      className="bg-[#1A1A1A] rounded-2xl border border-white/[0.08] p-4 shadow-xl shadow-black/30 w-full"
      aria-hidden="true"
    >
      {/* Score gauge + type */}
      <div className="flex items-center gap-3 mb-3">
        <ScoreRing score={MOCK_HOOK.score} />
        <div>
          <div className="text-[10px] font-semibold text-[--color-primary] uppercase tracking-wider mb-0.5">
            {MOCK_HOOK.type}
          </div>
          <div className="text-[10px] text-white/35 uppercase tracking-wider">{MOCK_HOOK.funnel}</div>
          <div className="text-[10px] text-white/25 font-mono mt-1">
            {MOCK_HOOK.startTime} → {MOCK_HOOK.endTime}
          </div>
        </div>
      </div>

      {/* Hook text */}
      <p className="text-[13px] text-white/75 leading-relaxed line-clamp-2">
        {MOCK_HOOK.text}
      </p>

      {/* Score dots */}
      <div className="flex items-center gap-1.5 mt-3">
        <div className="w-2 h-2 rounded-full bg-green-500" />
        <div className="w-2 h-2 rounded-full bg-[--color-primary]" />
        <div className="w-2 h-2 rounded-full bg-amber-400" />
        <span className="text-[10px] text-white/25 ml-1">High impact</span>
      </div>
    </div>
  );
}

/**
 * Static hero right panel used in the marketing homepage hero section.
 * Two stacked cards (Short preview + hook score card) with subtle rotation for depth.
 */
export const HeroHookPreview = memo(function HeroHookPreview() {
  return (
    <motion.div
      className="relative flex flex-col items-center gap-4"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.6, ease: "easeOut" }}
      aria-hidden="true"
    >
      {/* Background glow */}
      <div
        className="absolute inset-0 -z-10 rounded-3xl opacity-30"
        style={{
          background:
            "radial-gradient(ellipse at 50% 40%, rgba(232,74,47,0.12) 0%, transparent 70%)",
        }}
      />

      <div className="flex gap-4 items-start">
        {/* Short preview card — 1deg rotation */}
        <motion.div
          style={{ rotate: -1.5 }}
          whileHover={{ rotate: 0, y: -2 }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
        >
          <ShortPreviewCard />
        </motion.div>

        {/* Hook score card — max width 240px, slight counter-rotation */}
        <motion.div
          className="max-w-[240px] w-full"
          style={{ rotate: 1 }}
          whileHover={{ rotate: 0, y: -2 }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
        >
          <HookScoreCard />
        </motion.div>
      </div>

      {/* Floating stat badge */}
      <motion.div
        className="absolute -bottom-4 left-1/2 -translate-x-1/2 bg-[#1A1A1A] border border-white/[0.08] rounded-xl px-4 py-2 flex items-center gap-2 shadow-lg shadow-black/30"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.4 }}
      >
        <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
        <span className="text-[11px] text-white/50 font-medium">87 hooks analyzed today</span>
      </motion.div>
    </motion.div>
  );
});
