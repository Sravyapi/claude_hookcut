"use client";

import { useState, useCallback, useMemo, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Hook, CaptionStyle } from "@/lib/types";
import { MAX_SELECTED_HOOKS } from "@/lib/constants";
import { HookCard } from "./hook-card";
import { HookTimeline, type TimelineHook } from "./hook-timeline";
import TrimSlider, { parseTimestamp } from "./trim-slider";
import { staggerContainer, fadeUpItem } from "@/lib/motion";

// ─── Caption style config ─────────────────────────────────────────────────────

const CAPTION_STYLE_OPTIONS: {
  value: CaptionStyle;
  label: string;
  description: string;
  preview: { font: string; color: string; bg: string };
}[] = [
  {
    value: "clean",
    label: "Clean",
    description: "Professional & readable",
    preview: { font: "font-sans", color: "text-white", bg: "bg-black/60" },
  },
  {
    value: "bold",
    label: "Bold",
    description: "High-energy & impactful",
    preview: { font: "font-bold", color: "text-white", bg: "bg-black/70" },
  },
  {
    value: "neon",
    label: "Neon",
    description: "Trendy & eye-catching",
    preview: { font: "font-black", color: "text-cyan-400", bg: "bg-slate-950/70" },
  },
  {
    value: "minimal",
    label: "Minimal",
    description: "Subtle & elegant",
    preview: { font: "font-light", color: "text-white/80", bg: "bg-black/40" },
  },
];

// ─── Props ────────────────────────────────────────────────────────────────────

interface HooksStepProps {
  hooks: Hook[];
  videoTitle: string;
  regenerationCount: number;
  onSelectHooks: (
    hookIds: string[],
    captionStyle: string,
    timeOverrides: Record<string, { start_seconds: number; end_seconds: number }>
  ) => void;
  onRegenerate: () => void;
  isRegenerating: boolean;
  analysisElapsed?: number;
  /** Used to position timeline markers — pass video_duration_seconds from AnalyzeResponse */
  videoDurationSeconds?: number;
}

// ─── Component ────────────────────────────────────────────────────────────────

export const HooksStep = memo(function HooksStep({
  hooks,
  videoTitle,
  regenerationCount,
  onSelectHooks,
  onRegenerate,
  isRegenerating,
  analysisElapsed = 0,
  videoDurationSeconds = 0,
}: HooksStepProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [captionStyle, setCaptionStyle] = useState<CaptionStyle>("clean");
  const [timeOverrides, setTimeOverrides] = useState<
    Record<string, { start_seconds: number; end_seconds: number }>
  >({});
  const [activeHookId, setActiveHookId] = useState<string | null>(null);

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

  const handleHoverChange = useCallback((id: string | null) => setActiveHookId(id), []);

  const handleGenerate = useCallback(
    () => onSelectHooks(Array.from(selectedIds), captionStyle, timeOverrides),
    [onSelectHooks, selectedIds, captionStyle, timeOverrides]
  );

  const avgScore = useMemo(
    () => (hooks.length > 0 ? hooks.reduce((s, h) => s + h.attention_score, 0) / hooks.length : 0),
    [hooks]
  );

  const selectedHooks = useMemo(
    () => hooks.filter((h) => selectedIds.has(h.id)),
    [hooks, selectedIds]
  );

  const timelineHooks: TimelineHook[] = useMemo(
    () =>
      hooks.map((h) => ({
        id: h.id,
        start_time: h.start_time,
        attention_score: h.attention_score,
        rank: h.rank,
      })),
    [hooks]
  );

  return (
    <div className="max-w-4xl mx-auto">
      {/* ── Header ── */}
      <motion.div
        className="mb-6"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
      >
        <div className="flex items-center gap-2 mb-1">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span className="text-xs text-emerald-400 font-medium">Analysis Complete</span>
        </div>
        <p className="text-sm text-white/40 truncate max-w-lg">{videoTitle}</p>
      </motion.div>

      {/* ── Hook Discovery Timeline ── */}
      <motion.div
        className="bg-[--color-surface-1] border border-[--color-border-def] rounded-2xl px-5 pt-4 pb-3 mb-6"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.05 }}
      >
        <HookTimeline
          hooks={timelineHooks}
          durationSeconds={videoDurationSeconds}
          activeHookId={activeHookId}
          className="mb-1"
        />
        {/* 1-line status bar */}
        <p className="text-[11px] text-[--color-muted] font-mono">
          {hooks.length} hook{hooks.length !== 1 ? "s" : ""} found
          {" · "}
          Avg {avgScore.toFixed(1)}
          {analysisElapsed > 0 && ` · Analyzed in ${analysisElapsed}s`}
        </p>
      </motion.div>

      {/* ── Selection hint ── */}
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

      {/* ── Hook cards ── */}
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
              onHoverChange={handleHoverChange}
            />
          </motion.div>
        ))}
      </motion.div>

      {/* ── Caption style picker (visible when hooks selected) ── */}
      <AnimatePresence>
        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-5 overflow-hidden"
          >
            <p className="text-[11px] text-[--color-muted] uppercase tracking-wider mb-2.5 font-semibold">
              Caption Style
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {CAPTION_STYLE_OPTIONS.map((opt) => (
                <CaptionStyleCard
                  key={opt.value}
                  option={opt}
                  selected={captionStyle === opt.value}
                  onSelect={setCaptionStyle}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Trim controls ── */}
      <AnimatePresence>
        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 overflow-hidden"
          >
            <p className="text-[11px] text-[--color-muted] uppercase tracking-wider mb-2.5 font-semibold">
              Trim Boundaries
            </p>
            <div className="space-y-2">
              {selectedHooks.map((h) => {
                const origStart = parseTimestamp(h.start_time);
                const origEnd = parseTimestamp(h.end_time);
                const override = timeOverrides[h.id];
                return (
                  <div
                    key={h.id}
                    className="bg-[--color-surface-1] border border-[--color-border-def] rounded-xl p-3 flex items-center gap-3"
                  >
                    <span className="text-[10px] font-bold text-[--color-primary]/60 uppercase font-mono shrink-0">
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

      {/* ── Sticky action bar ── */}
      <div className="sticky bottom-0 pt-4 pb-6">
        <div
          className="rounded-2xl p-4 flex items-center justify-between gap-4"
          style={{
            background: "rgba(17,17,17,0.92)",
            backdropFilter: "blur(20px) saturate(1.4)",
            border: "1px solid rgba(255,255,255,0.06)",
            boxShadow: "0 -8px 40px rgba(0,0,0,0.5)",
          }}
        >
          {/* Left: selection chips */}
          <div className="flex items-center gap-2 min-w-0 flex-1">
            {selectedIds.size === 0 ? (
              <span className="text-xs text-white/25">No hooks selected</span>
            ) : (
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-xs text-white/40 shrink-0 font-mono">
                  {selectedIds.size}/{MAX_SELECTED_HOOKS}
                </span>
                <AnimatePresence>
                  {selectedHooks.map((h) => (
                    <motion.span
                      key={h.id}
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.8, opacity: 0 }}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-[--color-primary]/15 text-[--color-primary] border border-[--color-primary]/20 truncate max-w-[110px]"
                      title={h.hook_text}
                    >
                      #{h.rank} {h.hook_type}
                    </motion.span>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>

          {/* Right: actions */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={onRegenerate}
              disabled={isRegenerating}
              className="btn-secondary text-sm flex items-center gap-2"
            >
              {isRegenerating ? (
                <>
                  <svg className="w-4 h-4 spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="30 70" />
                  </svg>
                  Regenerating…
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Regenerate
                  {regenerationCount > 0 && (
                    <span className="text-white/25 text-[10px]">(fee)</span>
                  )}
                </>
              )}
            </button>

            <button
              onClick={handleGenerate}
              disabled={selectedIds.size === 0}
              className="btn-primary text-sm flex items-center gap-2"
            >
              Generate {selectedIds.size > 0 ? selectedIds.size : ""}{" "}
              {selectedIds.size === 1 ? "Short" : "Shorts"}
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

// ─── Caption Style Card subcomponent ─────────────────────────────────────────

interface CaptionStyleCardProps {
  option: (typeof CAPTION_STYLE_OPTIONS)[number];
  selected: boolean;
  onSelect: (v: CaptionStyle) => void;
}

const CaptionStyleCard = memo(function CaptionStyleCard({
  option,
  selected,
  onSelect,
}: CaptionStyleCardProps) {
  const handleClick = useCallback(() => onSelect(option.value), [onSelect, option.value]);

  return (
    <button
      onClick={handleClick}
      className={`relative rounded-xl p-3 text-left transition-all ${
        selected
          ? "ring-2 ring-[--color-primary] bg-[--color-primary]/10"
          : "bg-[--color-surface-1] border border-[--color-border-def] hover:border-[--color-border-str]"
      }`}
      aria-pressed={selected}
    >
      <div className={`rounded-lg px-3 py-2 mb-2 ${option.preview.bg}`}>
        <span className={`text-sm ${option.preview.font} ${option.preview.color} leading-tight`}>
          Sample Text
        </span>
      </div>
      <div className="text-[13px] font-medium text-white/80">{option.label}</div>
      <div className="text-[10px] text-[--color-muted]">{option.description}</div>
      {selected && (
        <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-[--color-primary] flex items-center justify-center">
          <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
      )}
    </button>
  );
});
