"use client";

import { useState, useCallback, useEffect, useRef, useMemo, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Hook, CaptionStyle } from "../lib/types";
import { MAX_SELECTED_HOOKS } from "../lib/constants";
import HookCard from "./hook-card";
import TrimSlider, { parseTimestamp } from "./trim-slider";
import { staggerContainer, fadeUpItem } from "../lib/motion";

const CAPTION_STYLE_OPTIONS: { value: CaptionStyle; label: string; description: string; preview: { font: string; color: string; bg: string } }[] = [
  { value: "clean", label: "Clean", description: "Professional & readable", preview: { font: "font-sans", color: "text-white", bg: "bg-black/60" } },
  { value: "bold", label: "Bold", description: "High-energy & impactful", preview: { font: "font-bold", color: "text-white", bg: "bg-black/70" } },
  { value: "neon", label: "Neon", description: "Trendy & eye-catching", preview: { font: "font-black", color: "text-cyan-400", bg: "bg-indigo-950/70" } },
  { value: "minimal", label: "Minimal", description: "Subtle & elegant", preview: { font: "font-light", color: "text-white/80", bg: "bg-black/40" } },
];

interface HooksStepProps {
  hooks: Hook[];
  videoTitle: string;
  regenerationCount: number;
  onSelectHooks: (hookIds: string[], captionStyle: string, timeOverrides: Record<string, { start_seconds: number; end_seconds: number }>) => void;
  onRegenerate: () => void;
  isRegenerating: boolean;
  analysisElapsed?: number;
}

const COUNT_UP_MAX_DURATION = 2000; // Hard cap: snap to final value after 2s

function useCountUp(target: number, duration = 900) {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | undefined>(undefined);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    const start = performance.now();
    const tick = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setValue(target * eased);
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };
    rafRef.current = requestAnimationFrame(tick);

    // Safety timeout: snap to final value if animation runs too long
    timeoutRef.current = setTimeout(() => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      setValue(target);
    }, COUNT_UP_MAX_DURATION);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [target, duration]);

  return value;
}

export default memo(function HooksStep({
  hooks,
  videoTitle,
  regenerationCount,
  onSelectHooks,
  onRegenerate,
  isRegenerating,
  analysisElapsed = 0,
}: HooksStepProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [captionStyle, setCaptionStyle] = useState<CaptionStyle>("clean");
  const [timeOverrides, setTimeOverrides] = useState<Record<string, { start_seconds: number; end_seconds: number }>>({});

  const toggleHook = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        setTimeOverrides((o) => {
          const copy = { ...o };
          delete copy[id];
          return copy;
        });
      } else if (next.size < MAX_SELECTED_HOOKS) {
        next.add(id);
      }
      return next;
    });
  }, []);

  const avgScore = useMemo(() => hooks.length > 0 ? hooks.reduce((sum, h) => sum + h.attention_score, 0) / hooks.length : 0, [hooks]);
  const topScore = useMemo(() => hooks.length > 0 ? Math.max(...hooks.map((h) => h.attention_score)) : 0, [hooks]);

  const animatedAvg = useCountUp(avgScore);
  const animatedTop = useCountUp(topScore);
  const animatedCount = useCountUp(hooks.length);

  const selectedHooks = useMemo(() => hooks.filter((h) => selectedIds.has(h.id)), [hooks, selectedIds]);

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <motion.div
        className="text-center mb-8"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/8 border border-emerald-500/15 text-emerald-400 text-xs font-medium mb-5">
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2.5}
              d="M5 13l4 4L19 7"
            />
          </svg>
          Analysis Complete
        </div>

        <h2 className="text-3xl font-bold text-white/90 mb-1">
          Hook Segments Found
        </h2>
        <p className="text-white/35 text-sm truncate max-w-md mx-auto">
          {videoTitle}
        </p>
      </motion.div>

      {/* Stats cards */}
      <motion.div
        className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <div className="glass-card rounded-2xl p-4 text-center">
          <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center mx-auto mb-2">
            <svg
              className="w-4 h-4 text-violet-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
          <div className="text-2xl font-bold gradient-text leading-none tabular-nums mb-1">
            {Math.round(animatedCount)}
          </div>
          <div className="text-[10px] text-white/25 uppercase tracking-wider">
            Hooks Found
          </div>
        </div>

        <div className="glass-card rounded-2xl p-4 text-center">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center mx-auto mb-2">
            <svg
              className="w-4 h-4 text-emerald-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="text-2xl font-bold text-emerald-400 leading-none tabular-nums mb-1">
            {animatedTop.toFixed(1)}
          </div>
          <div className="text-[10px] text-white/25 uppercase tracking-wider">
            Top Score
          </div>
        </div>

        <div className="glass-card rounded-2xl p-4 text-center">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center mx-auto mb-2">
            <svg
              className="w-4 h-4 text-purple-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <div className="text-2xl font-bold text-white/70 leading-none tabular-nums mb-1">
            {animatedAvg.toFixed(1)}
          </div>
          <div className="text-[10px] text-white/25 uppercase tracking-wider">
            Avg Score
          </div>
        </div>

        {analysisElapsed > 0 && (
          <div className="glass-card rounded-2xl p-4 text-center">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center mx-auto mb-2">
              <svg
                className="w-4 h-4 text-cyan-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="text-2xl font-bold text-cyan-400 leading-none tabular-nums mb-1">
              {analysisElapsed}s
            </div>
            <div className="text-[10px] text-white/25 uppercase tracking-wider">
              Analysis Time
            </div>
          </div>
        )}
      </motion.div>

      {/* Selection hint */}
      <AnimatePresence>
        {selectedIds.size === 0 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center text-xs text-white/25 mb-4"
          >
            Select up to {MAX_SELECTED_HOOKS} hooks to generate Shorts
          </motion.p>
        )}
      </AnimatePresence>

      {/* Hook cards — 2-column grid on desktop */}
      <motion.div
        className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8"
        variants={staggerContainer}
        initial="hidden"
        animate="show"
      >
        {hooks.map((hook) => (
          <motion.div key={hook.id} variants={fadeUpItem}>
            <HookCard
              hook={hook}
              selected={selectedIds.has(hook.id)}
              onToggle={toggleHook}
              disabled={selectedIds.size >= MAX_SELECTED_HOOKS}
            />
          </motion.div>
        ))}
      </motion.div>

      {/* Caption style picker — visible when hooks are selected */}
      <AnimatePresence>
        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 overflow-hidden"
          >
            <div className="text-xs text-white/30 uppercase tracking-wider mb-3 text-center">
              Caption Style
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {CAPTION_STYLE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setCaptionStyle(opt.value)}
                  className={`group relative rounded-xl p-3 text-left transition-all ${
                    captionStyle === opt.value
                      ? "ring-2 ring-violet-500 bg-violet-500/10"
                      : "glass-card hover:bg-white/[0.04]"
                  }`}
                >
                  {/* Preview bar */}
                  <div className={`rounded-lg px-3 py-2 mb-2 ${opt.preview.bg}`}>
                    <span className={`text-sm ${opt.preview.font} ${opt.preview.color} leading-tight`}>
                      Sample Text
                    </span>
                  </div>
                  <div className="text-sm font-medium text-white/80">{opt.label}</div>
                  <div className="text-[10px] text-white/30">{opt.description}</div>
                  {captionStyle === opt.value && (
                    <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-violet-500 flex items-center justify-center">
                      <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Trim controls for selected hooks */}
      <AnimatePresence>
        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 overflow-hidden"
          >
            <div className="text-xs text-white/30 uppercase tracking-wider mb-3 text-center">
              Trim Boundaries
            </div>
            <div className="space-y-2">
              {selectedHooks.map((h) => {
                const origStart = parseTimestamp(h.start_time);
                const origEnd = parseTimestamp(h.end_time);
                const override = timeOverrides[h.id];
                return (
                  <div
                    key={h.id}
                    className="glass-card rounded-xl p-3 flex items-center gap-3"
                  >
                    <span className="text-[10px] font-bold text-violet-400/60 uppercase shrink-0">
                      #{h.rank}
                    </span>
                    <TrimSlider
                      startSeconds={override?.start_seconds ?? origStart}
                      endSeconds={override?.end_seconds ?? origEnd}
                      originalStart={origStart}
                      originalEnd={origEnd}
                      onChange={(start, end) =>
                        setTimeOverrides((prev) => ({
                          ...prev,
                          [h.id]: { start_seconds: start, end_seconds: end },
                        }))
                      }
                    />
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sticky action bar with gradient backdrop */}
      <div className="sticky bottom-0 pt-4 pb-6">
        <div
          className="rounded-2xl p-4 flex items-center justify-between gap-4 shadow-[0_-8px_40px_rgba(0,0,0,0.5)]"
          style={{
            background: "rgba(6, 6, 14, 0.88)",
            backdropFilter: "blur(24px) saturate(1.4)",
            border: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          {/* Left: selection chips */}
          <div className="flex items-center gap-2 min-w-0 flex-1">
            {selectedIds.size === 0 ? (
              <span className="text-xs text-white/25">No hooks selected</span>
            ) : (
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-xs text-white/40 shrink-0">
                  {selectedIds.size}/{MAX_SELECTED_HOOKS}
                </span>
                <AnimatePresence>
                  {selectedHooks.map((h) => (
                    <motion.span
                      key={h.id}
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.8, opacity: 0 }}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-300 border border-violet-500/20 truncate max-w-[100px]"
                      title={h.hook_text}
                    >
                      #{h.rank} {h.hook_type}
                    </motion.span>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>

          {/* Right: action buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={onRegenerate}
              disabled={isRegenerating}
              className="btn-secondary text-sm flex items-center gap-2"
            >
              {isRegenerating ? (
                <>
                  <svg
                    className="w-4 h-4 spin"
                    viewBox="0 0 24 24"
                    fill="none"
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
                  Regenerating...
                </>
              ) : (
                <>
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Regenerate
                  {regenerationCount > 0 && (
                    <span className="text-white/25 text-[10px]">(fee)</span>
                  )}
                </>
              )}
            </button>

            <button
              onClick={() => onSelectHooks(Array.from(selectedIds), captionStyle, timeOverrides)}
              disabled={selectedIds.size === 0}
              className="btn-primary text-sm flex items-center gap-2"
            >
              Generate {selectedIds.size}{" "}
              {selectedIds.size === 1 ? "Short" : "Shorts"}
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});
