"use client";

import { memo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Hook } from "@/lib/types";
import { HOOK_TYPE_COLORS, FUNNEL_ROLE_LABELS } from "@/lib/constants";
import { getScoreColor } from "@/lib/utils";
import { ScorePopover } from "./score-popover";

// ─── Props ────────────────────────────────────────────────────────────────────

interface HookCardProps {
  hook: Hook;
  selected: boolean;
  onToggle: (id: string) => void;
  disabled: boolean;
  /** Called with hook id on enter, null on leave — parent uses this to pulse timeline marker */
  onHoverChange?: (id: string | null) => void;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getGradeLabel(score: number): string {
  if (score >= 8.1) return "Exceptional";
  if (score >= 6.5) return "High Impact";
  if (score >= 4) return "Moderate";
  return "Needs Work";
}

// ─── Score Gauge ──────────────────────────────────────────────────────────────

function ScoreGauge({ score }: { score: number }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const { hex } = getScoreColor(score);
  const targetOffset = circumference - (score / 10) * circumference;

  return (
    <div className="flex flex-col items-center gap-1" aria-hidden="true">
      <div className="relative w-[88px] h-[88px]">
        <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
          <circle cx="40" cy="40" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="5" />
          <motion.circle
            cx="40"
            cy="40"
            r={radius}
            fill="none"
            stroke={hex}
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: targetOffset }}
            transition={{ type: "spring", stiffness: 55, damping: 18, delay: 0.15 }}
            style={{ filter: `drop-shadow(0 0 7px ${hex}55)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white font-mono leading-none tabular-nums">
            {score.toFixed(1)}
          </span>
          <span className="text-[9px] text-white/30 uppercase tracking-wider mt-0.5">score</span>
        </div>
      </div>
      <span className="text-[11px] font-semibold" style={{ color: hex }}>
        {getGradeLabel(score)}
      </span>
    </div>
  );
}

// ─── Insight Row ──────────────────────────────────────────────────────────────

interface InsightRowProps {
  label: string;
  text: string;
  labelColor: string;
  icon: React.ReactNode;
  accent?: boolean;
}

function InsightRow({ label, text, labelColor, icon, accent = false }: InsightRowProps) {
  return (
    <div
      className={`p-2.5 rounded-lg border ${
        accent
          ? "bg-emerald-500/[0.04] border-emerald-500/10"
          : "bg-[--color-border-sub] border-[--color-border-sub]"
      }`}
    >
      <div className={`flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider mb-0.5 ${labelColor}`}>
        <span aria-hidden="true">{icon}</span>
        {label}
      </div>
      <p className="text-[11px] text-white/50 leading-relaxed">{text}</p>
    </div>
  );
}

// ─── Icon helpers ─────────────────────────────────────────────────────────────

function PlatformIcon() {
  return (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}

function PsychIcon() {
  return (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  );
}

function TipIcon() {
  return (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
    </svg>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export const HookCard = memo(function HookCard({
  hook,
  selected,
  onToggle,
  disabled,
  onHoverChange,
}: HookCardProps) {
  const typeColor = HOOK_TYPE_COLORS[hook.hook_type] ?? "bg-white/10 text-white/70 border-white/20";
  const funnelLabel = FUNNEL_ROLE_LABELS[hook.funnel_role] ?? hook.funnel_role;

  const handleMouseEnter = useCallback(
    () => onHoverChange?.(hook.id),
    [onHoverChange, hook.id]
  );
  const handleMouseLeave = useCallback(
    () => onHoverChange?.(null),
    [onHoverChange]
  );
  const handleClick = useCallback(() => {
    if (!(disabled && !selected)) onToggle(hook.id);
  }, [disabled, selected, onToggle, hook.id]);
  const handleCheckboxChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.stopPropagation();
      onToggle(hook.id);
    },
    [onToggle, hook.id]
  );
  const handleCheckboxClick = useCallback((e: React.MouseEvent) => e.stopPropagation(), []);

  return (
    <motion.div
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`rounded-2xl cursor-pointer relative overflow-hidden border transition-colors duration-150 ${
        selected
          ? "bg-[--color-surface-2] border-[--color-primary]/40 ring-1 ring-[--color-primary]/20"
          : "bg-[--color-surface-1] border-[--color-border-def] hover:border-[--color-border-str] hover:bg-[--color-surface-2]"
      }`}
      animate={{
        scale: selected ? 1.005 : 1,
        boxShadow: selected ? "0 0 28px rgba(232,74,47,0.08)" : "none",
      }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      role="article"
      aria-label={`Hook ${hook.rank}: ${hook.hook_type}`}
    >
      {/* Selection badge */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 20 }}
            className="absolute top-3 right-3 w-6 h-6 rounded-full bg-[--color-primary] flex items-center justify-center z-10"
            style={{ boxShadow: "0 0 12px rgba(232,74,47,0.4)" }}
            aria-hidden="true"
          >
            <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="p-5">
        {/* ── Score gauge ── */}
        <div className="flex justify-center mb-4">
          <ScoreGauge score={hook.attention_score} />
        </div>

        {/* ── Hook type + funnel role ── */}
        <div className="flex flex-col items-center gap-1.5 mb-4">
          <div className="flex items-center gap-2 flex-wrap justify-center">
            <span className={`text-[11px] px-2.5 py-0.5 rounded-full border font-semibold tracking-wide ${typeColor}`}>
              {hook.hook_type.toUpperCase()}
            </span>
            {hook.is_composite && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400/80 border border-amber-500/15">
                Composite
              </span>
            )}
          </div>
          <span className="text-[11px] text-[--color-muted] text-center">
            {hook.funnel_role.replace(/_/g, " ").toUpperCase()} · {funnelLabel}
          </span>
        </div>

        {/* ── Hook text ── */}
        <p className="text-[15px] text-white/80 leading-relaxed line-clamp-3 mb-3">
          {hook.hook_text}
        </p>

        {/* ── Timestamp ── */}
        <div className="flex items-center justify-center gap-1.5 text-[12px] text-[--color-muted] font-mono mb-4">
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="tabular-nums">{hook.start_time} → {hook.end_time}</span>
        </div>

        {/* ── Divider ── */}
        <div className="border-t border-[--color-border-sub] mb-4" />

        {/* ── Insight rows ── */}
        <div className="space-y-2 mb-4" onClick={(e) => e.stopPropagation()}>
          <InsightRow
            label="Platform Dynamics"
            text={hook.platform_dynamics}
            labelColor="text-[--color-primary]/70"
            icon={<PlatformIcon />}
          />
          <InsightRow
            label="Viewer Psychology"
            text={hook.viewer_psychology}
            labelColor="text-blue-400/70"
            icon={<PsychIcon />}
          />
          {hook.improvement_suggestion && (
            <InsightRow
              label="Creator Tip"
              text={hook.improvement_suggestion}
              labelColor="text-emerald-400/70"
              icon={<TipIcon />}
              accent
            />
          )}
        </div>

        {/* ── Footer: dimensions popover + rank + checkbox ── */}
        <div
          className="flex items-center justify-between pt-3 border-t border-[--color-border-sub]"
          onClick={(e) => e.stopPropagation()}
        >
          <ScorePopover scores={hook.scores} />
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[--color-muted] uppercase tracking-wider font-mono">
              #{hook.rank}
            </span>
            <input
              type="checkbox"
              className="hook-checkbox"
              checked={selected}
              onChange={handleCheckboxChange}
              onClick={handleCheckboxClick}
              disabled={disabled && !selected}
              aria-label={`Select hook ${hook.rank}: ${hook.hook_type}`}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
});
