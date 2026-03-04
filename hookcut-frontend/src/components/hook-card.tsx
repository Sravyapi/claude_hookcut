"use client";

import { useState, memo, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Hook, HookScores } from "../lib/types";
import { HOOK_TYPE_COLORS, HOOK_TYPE_DESCRIPTIONS, FUNNEL_ROLE_LABELS } from "../lib/constants";
import { getScoreColor } from "../lib/utils";
import ScoreBar, { SCORE_LABELS } from "./score-bar";

interface HookCardProps {
  hook: Hook;
  selected: boolean;
  onToggle: (id: string) => void;
  disabled: boolean;
}

function ScoreGauge({ score }: { score: number }) {
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const { hex: color } = getScoreColor(score);
  const targetOffset = circumference - (score / 10) * circumference;

  return (
    <div className="relative w-[72px] h-[72px] shrink-0">
      <svg viewBox="0 0 64 64" className="w-full h-full -rotate-90">
        {/* Track */}
        <circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.04)"
          strokeWidth="4"
        />
        {/* Animated fill with glow */}
        <motion.circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: targetOffset }}
          transition={{ type: "spring", stiffness: 60, damping: 18, delay: 0.2 }}
          style={{ filter: `drop-shadow(0 0 6px ${color}60)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-white/90 leading-none tabular-nums">
          {score.toFixed(1)}
        </span>
        <span className="text-[8px] text-white/30 uppercase tracking-wider mt-0.5">
          score
        </span>
      </div>
    </div>
  );
}

export default memo(function HookCard({
  hook,
  selected,
  onToggle,
  disabled,
}: HookCardProps) {
  const [scoresOpen, setScoresOpen] = useState(false);

  const typeColor =
    HOOK_TYPE_COLORS[hook.hook_type] || "bg-white/10 text-white/70 border-white/20";
  const funnelLabel = FUNNEL_ROLE_LABELS[hook.funnel_role] || hook.funnel_role;
  const typeDescription = HOOK_TYPE_DESCRIPTIONS[hook.hook_type] || "";

  // Top 2 strongest scores for highlight + top 3 dots for collapsed preview
  const sortedScores = useMemo(
    () => (Object.entries(hook.scores) as [keyof HookScores, number][]).sort(([, a], [, b]) => b - a),
    [hook.scores]
  );
  const topScores = sortedScores.slice(0, 3);
  const top2Scores = sortedScores.slice(0, 2);

  return (
    <motion.div
      onClick={() => !(disabled && !selected) && onToggle(hook.id)}
      className={`glass rounded-2xl cursor-pointer relative overflow-hidden ${
        selected
          ? "ring-2 ring-violet-500/40 bg-violet-500/[0.04] border-violet-500/20"
          : "hover:bg-white/[0.04] hover:border-white/10"
      }`}
      animate={{
        scale: selected ? 1.005 : 1,
        boxShadow: selected
          ? "0 0 32px rgba(139,92,246,0.10)"
          : "none",
      }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
    >
      {/* Pop-in checkmark badge on selection */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 20 }}
            className="absolute top-3 right-3 w-6 h-6 rounded-full bg-violet-500 flex items-center justify-center z-10 shadow-lg shadow-violet-500/40"
          >
            <svg
              className="w-3.5 h-3.5 text-white"
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
          </motion.div>
        )}
      </AnimatePresence>

      <div className="p-5 flex gap-4">
        {/* Left: Checkbox + Rank */}
        <div className="flex flex-col items-center gap-2 pt-0.5">
          <input
            type="checkbox"
            className="hook-checkbox"
            checked={selected}
            onChange={(e) => {
              e.stopPropagation();
              onToggle(hook.id);
            }}
            onClick={(e) => e.stopPropagation()}
            disabled={disabled && !selected}
            aria-label={`Select hook ${hook.rank}: ${hook.hook_type}`}
          />
          <span className="text-[10px] font-bold text-violet-400/60 uppercase tracking-wider">
            #{hook.rank}
          </span>
        </div>

        {/* Center: Content */}
        <div className="flex-1 min-w-0">
          {/* Tags row with stagger */}
          <motion.div
            className="flex items-center gap-1.5 flex-wrap mb-3"
            initial="hidden"
            animate="show"
            variants={{
              hidden: {},
              show: { transition: { staggerChildren: 0.06 } },
            }}
          >
            <motion.span
              variants={{ hidden: { opacity: 0, x: -8 }, show: { opacity: 1, x: 0 } }}
              className={`text-[11px] px-2.5 py-0.5 rounded-full border ${typeColor}`}
            >
              {hook.hook_type}
            </motion.span>
            <motion.span
              variants={{ hidden: { opacity: 0, x: -8 }, show: { opacity: 1, x: 0 } }}
              className="text-[11px] px-2.5 py-0.5 rounded-full bg-white/[0.04] text-white/40 border border-white/[0.06]"
            >
              {funnelLabel}
            </motion.span>
            {hook.is_composite && (
              <motion.span
                variants={{ hidden: { opacity: 0, x: -8 }, show: { opacity: 1, x: 0 } }}
                className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400/80 border border-amber-500/15"
              >
                Composite
              </motion.span>
            )}
          </motion.div>

          {/* Hook type description */}
          {typeDescription && (
            <p className="text-[11px] text-white/30 italic mb-3 -mt-1">
              {typeDescription}
            </p>
          )}

          {/* Hook text with decorative quotation mark */}
          <div className="relative mb-3">
            <span className="absolute -top-3 -left-1 text-6xl text-violet-500/10 font-serif leading-none select-none pointer-events-none">
              &ldquo;
            </span>
            <p className="text-[15px] text-white/80 leading-relaxed pl-2">
              {hook.hook_text}
            </p>
          </div>

          {/* Time range + top 2 score highlights */}
          <div className="flex items-center gap-3 text-xs text-white/30 mb-3 flex-wrap">
            <div className="flex items-center gap-1.5">
              <svg
                className="w-3.5 h-3.5"
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
              <span className="tabular-nums">
                {hook.start_time} &ndash; {hook.end_time}
              </span>
            </div>
            <span className="w-px h-3 bg-white/10" />
            <div className="flex items-center gap-2">
              {top2Scores.map(([key, val]) => (
                <span key={key} className="flex items-center gap-1">
                  <span className={`w-1.5 h-1.5 rounded-full ${getScoreColor(val).dot}`} />
                  <span className="text-white/45 tabular-nums">{(SCORE_LABELS[key] ?? key)} {val.toFixed(1)}</span>
                </span>
              ))}
            </div>
          </div>

          {/* Always-visible insights */}
          <div className="grid gap-2 mb-3" onClick={(e) => e.stopPropagation()}>
            <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <div className="text-[10px] text-violet-400/50 uppercase tracking-wider mb-0.5 font-medium">
                Platform Dynamics
              </div>
              <p className="text-[11px] text-white/50 leading-relaxed">
                {hook.platform_dynamics}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
              <div className="text-[10px] text-violet-400/50 uppercase tracking-wider mb-0.5 font-medium">
                Viewer Psychology
              </div>
              <p className="text-[11px] text-white/50 leading-relaxed">
                {hook.viewer_psychology}
              </p>
            </div>
            {hook.improvement_suggestion && (
              <div className="p-2.5 rounded-lg bg-emerald-500/[0.04] border border-emerald-500/10">
                <div className="text-[10px] text-emerald-400/60 uppercase tracking-wider mb-0.5 font-medium">
                  Creator Tip
                </div>
                <p className="text-[11px] text-emerald-300/60 leading-relaxed">
                  {hook.improvement_suggestion}
                </p>
              </div>
            )}
          </div>

          {/* Scores — collapsed by default, expand on click */}
          <div onClick={(e) => e.stopPropagation()}>
            {!scoresOpen ? (
              <button
                onClick={() => setScoresOpen(true)}
                className="flex items-center gap-2 text-xs text-white/30 hover:text-white/50 transition-colors"
              >
                <div className="flex items-center gap-1">
                  {topScores.map(([key, val]) => (
                    <div
                      key={key}
                      className={`w-2 h-2 rounded-full ${getScoreColor(val).dot}`}
                      title={`${SCORE_LABELS[key] ?? key}: ${val.toFixed(1)}`}
                    />
                  ))}
                </div>
                <span>Show all scores</span>
                <svg
                  className="w-3 h-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>
            ) : (
              <AnimatePresence>
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <ScoreBar scores={hook.scores} />
                  <button
                    onClick={() => setScoresOpen(false)}
                    className="mt-2 text-xs text-white/25 hover:text-white/40 transition-colors flex items-center gap-1"
                  >
                    <svg
                      className="w-3 h-3"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 15l7-7 7 7"
                      />
                    </svg>
                    Hide scores
                  </button>
                </motion.div>
              </AnimatePresence>
            )}
          </div>
        </div>

        {/* Right: Score gauge (desktop) */}
        <div className="hidden sm:block">
          <ScoreGauge score={hook.attention_score} />
        </div>
      </div>

      {/* Mobile score */}
      <div className="sm:hidden flex items-center justify-between px-5 pb-4">
        <span className="text-[10px] text-white/30 uppercase tracking-wider">
          Attention Score
        </span>
        <span className="text-lg font-bold gradient-text tabular-nums">
          {hook.attention_score.toFixed(1)}
        </span>
      </div>
    </motion.div>
  );
});
