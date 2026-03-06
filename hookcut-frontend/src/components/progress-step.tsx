"use client";

import { useEffect, useState, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ProgressStepProps {
  progress: number;
  videoTitle: string;
  startTime: number;
}

// ─── Stage config ─────────────────────────────────────────────────────────────

const STAGES = [
  {
    id: "transcript",
    label: "Reading transcript",
    detail: "Parsing the full transcript to map out what was said and when.",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    min: 0,
    max: 33,
  },
  {
    id: "hooks",
    label: "Detecting hooks",
    detail: "Finding moments that stop scrollers — curiosity gaps, stakes, pattern interrupts.",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    min: 33,
    max: 66,
  },
  {
    id: "ranking",
    label: "Scoring & ranking",
    detail: "Rating each hook across 7 dimensions to surface your top performers.",
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    min: 66,
    max: 100,
  },
] as const;

function getStageIndex(progress: number): number {
  if (progress >= 66) return 2;
  if (progress >= 33) return 1;
  return 0;
}

// ─── Pulsing orb ──────────────────────────────────────────────────────────────

function PulsingOrb({ progress }: { progress: number }) {
  return (
    <div className="relative flex items-center justify-center w-32 h-32 mx-auto mb-8">
      {/* Outer rings */}
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="absolute rounded-full border border-violet-500/20"
          style={{ width: 56 + i * 24, height: 56 + i * 24 }}
          animate={{ scale: [1, 1.12, 1], opacity: [0.4, 0.15, 0.4] }}
          transition={{
            duration: 2.4,
            repeat: Infinity,
            delay: i * 0.5,
            ease: "easeInOut",
          }}
        />
      ))}
      {/* Core */}
      <div className="relative w-14 h-14 rounded-full bg-gradient-to-br from-violet-600/40 to-purple-700/40 border border-violet-500/30 backdrop-blur-sm flex items-center justify-center"
        style={{ boxShadow: "0 0 32px rgba(139,92,246,0.25)" }}>
        <svg className="w-6 h-6 text-violet-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        {/* Progress arc overlay */}
        <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r="25" fill="none" stroke="rgba(139,92,246,0.12)" strokeWidth="2" />
          <motion.circle
            cx="28" cy="28" r="25"
            fill="none"
            stroke="rgb(139,92,246)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 25}`}
            animate={{ strokeDashoffset: 2 * Math.PI * 25 * (1 - progress / 100) }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </svg>
      </div>
    </div>
  );
}

// ─── Stage card ───────────────────────────────────────────────────────────────

interface StageCardProps {
  label: string;
  icon: React.ReactNode;
  isDone: boolean;
  isActive: boolean;
  isPending: boolean;
  fillRatio: number;
}

const StageCard = memo(function StageCard({
  label, icon, isDone, isActive, isPending, fillRatio,
}: StageCardProps) {
  return (
    <div
      className={`relative flex flex-col items-center gap-2 p-4 rounded-2xl border transition-all duration-500 ${
        isActive
          ? "border-violet-500/30 bg-violet-500/8"
          : isDone
          ? "border-emerald-500/20 bg-emerald-500/5"
          : "border-white/5 bg-white/[0.02]"
      }`}
    >
      {/* Icon */}
      <div
        className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-500 ${
          isDone
            ? "bg-emerald-500/15 text-emerald-400"
            : isActive
            ? "bg-violet-500/20 text-violet-300"
            : "bg-white/5 text-white/20"
        }`}
      >
        {isDone ? (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          icon
        )}
      </div>

      {/* Label */}
      <span
        className={`text-[11px] font-medium text-center leading-tight transition-colors duration-500 ${
          isDone ? "text-white/40" : isActive ? "text-white/80" : "text-white/20"
        }`}
      >
        {label}
      </span>

      {/* Mini progress bar */}
      <div className="w-full h-[3px] rounded-full bg-white/5 overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${isDone ? "bg-emerald-500" : "bg-violet-500"}`}
          initial={{ width: "0%" }}
          animate={{ width: `${fillRatio * 100}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        />
      </div>

      {/* Active pulse dot */}
      {isActive && (
        <div className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
      )}
    </div>
  );
});

// ─── Main Component ───────────────────────────────────────────────────────────

export const ProgressStep = memo(function ProgressStep({
  progress,
  videoTitle,
  startTime,
}: ProgressStepProps) {  // stage prop removed — progress value drives stage derivation internally
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startTime) return;
    const tick = () => setElapsed(Math.floor((Date.now() - startTime) / 1000));
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [startTime]);

  const elapsedFormatted = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, "0")}`;
  const activeIdx = getStageIndex(progress);
  const activeStage = STAGES[activeIdx];

  return (
    <motion.div
      className="max-w-sm mx-auto flex flex-col items-center"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Pulsing orb with progress arc */}
      <PulsingOrb progress={progress} />

      {/* Active stage label */}
      <AnimatePresence mode="wait">
        <motion.p
          key={activeStage.id}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.3 }}
          className="text-base font-semibold text-white/85 mb-1 text-center"
        >
          {activeStage.label}
        </motion.p>
      </AnimatePresence>

      {/* Stage detail */}
      <AnimatePresence mode="wait">
        <motion.p
          key={activeStage.id + "-detail"}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="text-[13px] text-white/35 text-center leading-relaxed mb-6 px-4"
        >
          {activeStage.detail}
        </motion.p>
      </AnimatePresence>

      {/* Video being analyzed */}
      {videoTitle && (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/8 mb-8 max-w-full">
          <svg className="w-3.5 h-3.5 text-red-400/70 shrink-0" viewBox="0 0 24 24" fill="currentColor">
            <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
          </svg>
          <span className="text-[11px] text-white/40 truncate max-w-[220px]">{videoTitle}</span>
        </div>
      )}

      {/* 3-stage cards */}
      <div className="grid grid-cols-3 gap-2.5 w-full mb-6">
        {STAGES.map((s, i) => {
          const isDone = progress >= s.max;
          const isActive = !isDone && progress >= s.min;
          const fillRatio = Math.max(0, Math.min(1, (progress - s.min) / (s.max - s.min)));
          return (
            <StageCard
              key={s.id}
              label={s.label}
              icon={s.icon}
              isDone={isDone}
              isActive={isActive}
              isPending={i > activeIdx}
              fillRatio={fillRatio}
            />
          );
        })}
      </div>

      {/* Footer: elapsed + progress */}
      <div className="flex items-center gap-3 text-[11px] text-white/20 font-mono">
        <span className="tabular-nums text-violet-400/50 font-medium">{progress}%</span>
        {elapsed > 0 && (
          <>
            <span className="w-px h-3 bg-white/10" />
            <svg className="w-3 h-3 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="tabular-nums">{elapsedFormatted}</span>
          </>
        )}
      </div>
    </motion.div>
  );
});

export default ProgressStep;
