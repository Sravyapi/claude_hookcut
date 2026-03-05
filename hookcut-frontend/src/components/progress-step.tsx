"use client";

import { useEffect, useState, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fadeUp } from "@/lib/motion";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ProgressStepProps {
  stage: string;
  progress: number;
  videoTitle: string;
  startTime: number;
}

// ─── Stage config ─────────────────────────────────────────────────────────────

const STAGES = [
  {
    id: "transcript",
    label: "Analyzing transcript",
    activeLabel: "Analyzing transcript…",
    min: 0,
    max: 33,
  },
  {
    id: "hooks",
    label: "Detecting hook moments",
    activeLabel: "Detecting hook moments…",
    min: 33,
    max: 66,
  },
  {
    id: "ranking",
    label: "Ranking engagement",
    activeLabel: "Ranking engagement potential…",
    min: 66,
    max: 100,
  },
] as const;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getStageProgress(progress: number, min: number, max: number): number {
  const range = max - min;
  if (range === 0) return 0;
  return Math.max(0, Math.min(1, (progress - min) / range));
}

function getActiveLabel(progress: number): string {
  if (progress >= 66) return STAGES[2].activeLabel;
  if (progress >= 33) return STAGES[1].activeLabel;
  return STAGES[0].activeLabel;
}

// ─── Progress Segment Row ─────────────────────────────────────────────────────

interface SegmentProps {
  label: string;
  fillRatio: number;
  isDone: boolean;
  isActive: boolean;
}

const ProgressSegment = memo(function ProgressSegment({
  label,
  fillRatio,
  isDone,
  isActive,
}: SegmentProps) {
  const barColor = isDone
    ? "bg-emerald-500"
    : "bg-[--color-primary]";

  return (
    <div className="flex items-center gap-3">
      {/* Status dot */}
      <div className="w-4 h-4 shrink-0 flex items-center justify-center">
        {isDone ? (
          <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
        ) : isActive ? (
          <div className="w-1.5 h-1.5 rounded-full bg-[--color-primary] animate-pulse" />
        ) : (
          <div className="w-1.5 h-1.5 rounded-full bg-white/15" />
        )}
      </div>

      {/* Label */}
      <span
        className={`text-[12px] w-[180px] shrink-0 transition-colors duration-300 ${
          isDone
            ? "text-white/50"
            : isActive
              ? "text-white/80 font-medium"
              : "text-white/25"
        }`}
      >
        {label}
      </span>

      {/* Bar track */}
      <div className="flex-1 h-[5px] rounded-full bg-white/[0.06] overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${barColor}`}
          initial={{ width: "0%" }}
          animate={{ width: `${fillRatio * 100}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        />
      </div>

      {/* Pct */}
      <span
        className={`text-[11px] font-mono w-8 text-right tabular-nums shrink-0 transition-colors duration-300 ${
          isDone ? "text-emerald-500" : isActive ? "text-[--color-primary]" : "text-white/15"
        }`}
      >
        {Math.round(fillRatio * 100)}%
      </span>
    </div>
  );
});

// ─── Main Component ───────────────────────────────────────────────────────────

export const ProgressStep = memo(function ProgressStep({
  progress,
  videoTitle,
  startTime,
}: ProgressStepProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startTime) return;
    const tick = () => setElapsed(Math.floor((Date.now() - startTime) / 1000));
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [startTime]);

  const activeLabel = getActiveLabel(progress);
  const elapsedFormatted = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, "0")}`;

  return (
    <motion.div
      className="max-w-md mx-auto"
      variants={fadeUp}
      initial="hidden"
      animate="show"
    >
      {/* Pulsing indicator */}
      <div className="flex items-center justify-center gap-2 mb-8">
        <div className="w-2 h-2 rounded-full bg-[--color-primary] animate-pulse" />
        <AnimatePresence mode="wait">
          <motion.span
            key={activeLabel}
            initial={{ opacity: 0, y: 3 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -3 }}
            transition={{ duration: 0.25 }}
            className="text-sm text-[--color-primary] font-medium"
          >
            {activeLabel}
          </motion.span>
        </AnimatePresence>
      </div>

      {/* Title */}
      <p className="text-[13px] text-white/35 truncate text-center mb-8 max-w-sm mx-auto">
        {videoTitle}
      </p>

      {/* 3-stage labeled bar stack */}
      <div className="space-y-4 mb-6">
        {STAGES.map((s) => {
          const fillRatio = getStageProgress(progress, s.min, s.max);
          const isDone = progress >= s.max;
          const isActive = !isDone && progress >= s.min;
          return (
            <ProgressSegment
              key={s.id}
              label={s.label}
              fillRatio={fillRatio}
              isDone={isDone}
              isActive={isActive}
            />
          );
        })}
      </div>

      {/* Elapsed timer */}
      <div className="flex items-center justify-center gap-3 text-[11px] text-white/25 font-mono">
        <span className="tabular-nums">{progress}%</span>
        {elapsed > 0 && (
          <>
            <span className="w-px h-3 bg-white/10" />
            <span className="tabular-nums">{elapsedFormatted} elapsed</span>
          </>
        )}
      </div>
    </motion.div>
  );
});

// Keep default export for backwards compatibility with page.tsx import
export default ProgressStep;
