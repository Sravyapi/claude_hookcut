"use client";

import { useState, useCallback, useMemo, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Scissors } from "lucide-react";
import type { Hook, CaptionStyle } from "@/lib/types";
import { MAX_SELECTED_HOOKS } from "@/lib/constants";
import { HookCard } from "./hook-card";
import TrimSlider, { parseTimestamp } from "./trim-slider";
import { staggerContainer, fadeUpItem } from "@/lib/motion";

// ─── Aspect ratio config ─────────────────────────────────────────────────────

type AspectRatio = "9:16" | "1:1" | "4:5";

const ASPECT_RATIO_OPTIONS: {
  value: AspectRatio;
  label: string;
  platform: string;
}[] = [
  { value: "9:16", label: "9:16", platform: "Shorts / TikTok" },
  { value: "1:1", label: "1:1", platform: "Instagram / X" },
  { value: "4:5", label: "4:5", platform: "Instagram / FB" },
];

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
    timeOverrides: Record<string, { start_seconds: number; end_seconds: number }>,
    aspectRatio: string
  ) => void;
  onRegenerate: () => void;
  isRegenerating: boolean;
  analysisElapsed?: number;
  sessionId?: string;
  onReset?: () => void;
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
  sessionId,
  onReset,
}: HooksStepProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [captionStyle, setCaptionStyle] = useState<CaptionStyle>("clean");
  const handleCaptionStyleChange = useCallback((v: CaptionStyle) => setCaptionStyle(v), []);
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("9:16");
  const handleAspectRatioChange = useCallback((v: AspectRatio) => setAspectRatio(v), []);
  const [timeOverrides, setTimeOverrides] = useState<
    Record<string, { start_seconds: number; end_seconds: number }>
  >({});

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

  const handleGenerate = useCallback(
    () => onSelectHooks(Array.from(selectedIds), captionStyle, timeOverrides, aspectRatio),
    [onSelectHooks, selectedIds, captionStyle, timeOverrides, aspectRatio]
  );

  const avgScore = useMemo(
    () => (hooks.length > 0 ? hooks.reduce((s, h) => s + h.attention_score, 0) / hooks.length : 0),
    [hooks]
  );

  const selectedHooks = useMemo(
    () => hooks.filter((h) => selectedIds.has(h.id)),
    [hooks, selectedIds]
  );

  return (
    <div className="max-w-5xl mx-auto">
      {/* ── Header ── */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
      >
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight mb-1">
              Hook Segments
            </h1>
            <p className="text-sm text-white/35 truncate max-w-lg">{videoTitle}</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <div className="flex items-center gap-3 text-xs text-white/30 font-mono tabular-nums">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                {hooks.length} hooks
              </span>
              <span>avg {avgScore.toFixed(1)}/10</span>
              {analysisElapsed > 0 && <span>{analysisElapsed}s</span>}
            </div>
            {onReset && (
              <button
                type="button"
                onClick={onReset}
                className="px-3 py-1.5 rounded-lg border border-white/[0.1] text-xs text-white/50 hover:text-white/80 hover:border-white/20 transition-colors"
              >
                New Video
              </button>
            )}
          </div>
        </div>
      </motion.div>

      {/* ── Selection hint ── */}
      <AnimatePresence>
        {selectedIds.size === 0 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center text-sm text-white/25 mb-6"
          >
            Select up to {MAX_SELECTED_HOOKS} hooks to generate Shorts
          </motion.p>
        )}
      </AnimatePresence>

      {/* ── Hook cards ── */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8"
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

      {/* ── Manual clipper CTA ── */}
      <div className="flex items-center gap-4 my-6">
        <div className="flex-1 h-px bg-white/10" />
        <span className="text-sm text-white/30">Or clip it yourself</span>
        <div className="flex-1 h-px bg-white/10" />
      </div>
      <div className="text-center mb-6">
        <a
          href={`/clip${sessionId ? `?session=${sessionId}` : ""}`}
          className="inline-flex items-center gap-2 text-sm text-violet-400 hover:text-violet-300 transition-colors"
        >
          <Scissors className="w-4 h-4" />
          Open Manual Clipper &rarr;
        </a>
      </div>

      {/* ── Caption style picker (visible when hooks selected) ── */}
      <AnimatePresence>
        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-5 overflow-hidden"
          >
            <p className="text-xs text-[--color-muted] uppercase tracking-wider mb-2.5 font-semibold">
              Caption Style
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {CAPTION_STYLE_OPTIONS.map((opt) => (
                <CaptionStyleCard
                  key={opt.value}
                  option={opt}
                  selected={captionStyle === opt.value}
                  onSelect={handleCaptionStyleChange}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Aspect ratio picker (visible when hooks selected) ── */}
      <AnimatePresence>
        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-5 overflow-hidden"
          >
            <p className="text-xs text-[--color-muted] uppercase tracking-wider mb-2.5 font-semibold">
              Aspect Ratio
            </p>
            <div className="flex gap-2">
              {ASPECT_RATIO_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleAspectRatioChange(opt.value)}
                  className={`relative rounded-xl px-4 py-2.5 text-left transition-all ${
                    aspectRatio === opt.value
                      ? "ring-2 ring-[--color-primary] bg-[--color-primary]/10"
                      : "bg-[--color-surface-1] border border-[--color-border-def] hover:border-[--color-border-str]"
                  }`}
                  aria-pressed={aspectRatio === opt.value}
                >
                  <div className="text-sm font-medium text-white/80">{opt.label}</div>
                  <div className="text-xs text-[--color-muted]">{opt.platform}</div>
                </button>
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
            <p className="text-xs text-[--color-muted] uppercase tracking-wider mb-2.5 font-semibold">
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
      <div className="text-xs text-[--color-muted]">{option.description}</div>
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
