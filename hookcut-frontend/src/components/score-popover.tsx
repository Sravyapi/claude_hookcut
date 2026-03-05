"use client";

import { memo, useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { HookScores } from "@/lib/types";
import { getScoreColor } from "@/lib/utils";

const SCORE_LABELS: Record<keyof HookScores, string> = {
  scroll_stop: "Scroll Stop",
  curiosity_gap: "Curiosity Gap",
  stakes_intensity: "Stakes",
  emotional_voltage: "Emotion",
  standalone_clarity: "Clarity",
  thematic_focus: "Focus",
  thought_completeness: "Completeness",
};

export { SCORE_LABELS };

interface ScorePopoverProps {
  scores: HookScores;
}

export const ScorePopover = memo(function ScorePopover({ scores }: ScorePopoverProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleToggle = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setOpen((v) => !v);
  }, []);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function handleOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [open]);

  const entries = Object.entries(SCORE_LABELS) as [keyof HookScores, string][];

  return (
    <div ref={containerRef} className="relative" onClick={(e) => e.stopPropagation()}>
      <button
        onClick={handleToggle}
        className="flex items-center gap-1 text-[11px] text-[--color-muted] hover:text-white/70 transition-colors duration-150"
        aria-expanded={open}
        aria-label="Show 7 scoring dimensions"
      >
        <span>7 dimensions</span>
        <svg
          className={`w-3 h-3 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.97 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute bottom-full left-0 mb-2 w-[240px] bg-[--color-surface-3] border border-[--color-border-str] rounded-xl p-3 shadow-xl shadow-black/40 z-50"
          >
            <p className="text-[10px] text-[--color-muted] uppercase tracking-wider font-semibold mb-2.5">
              Score Breakdown
            </p>
            <div className="space-y-1.5">
              {entries.map(([key, label], i) => {
                const value = scores[key] ?? 0;
                const { hex, gradient } = getScoreColor(value);
                return (
                  <div key={key} className="flex items-center gap-2">
                    <span className="text-[10px] text-white/40 w-[82px] shrink-0 text-right leading-none">
                      {label}
                    </span>
                    <div className="flex-1 h-[5px] rounded-full bg-white/[0.06] overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full bg-gradient-to-r ${gradient}`}
                        initial={{ width: "0%" }}
                        animate={{ width: `${(value / 10) * 100}%` }}
                        transition={{
                          type: "spring",
                          stiffness: 80,
                          damping: 20,
                          delay: i * 0.03,
                        }}
                      />
                    </div>
                    <span
                      className="text-[10px] font-mono w-6 text-right tabular-nums shrink-0"
                      style={{ color: hex }}
                    >
                      {value.toFixed(1)}
                    </span>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});
