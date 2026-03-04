"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import type { HookScores } from "../lib/types";
import { getScoreColor } from "../lib/utils";

const SCORE_LABELS: Record<string, string> = {
  scroll_stop: "Scroll Stop",
  curiosity_gap: "Curiosity",
  stakes_intensity: "Stakes",
  emotional_voltage: "Emotion",
  standalone_clarity: "Clarity",
  thematic_focus: "Focus",
  thought_completeness: "Complete",
};

export { SCORE_LABELS };

export default memo(function ScoreBar({
  scores,
  compact = false,
}: {
  scores: HookScores;
  compact?: boolean;
}) {
  const entries = Object.entries(SCORE_LABELS);

  if (compact) {
    return (
      <div className="flex items-center gap-3 flex-wrap">
        {entries.map(([key, label]) => {
          const value = scores[key as keyof HookScores] ?? 0;
          return (
            <div
              key={key}
              className="flex items-center gap-1.5"
              title={`${label}: ${value.toFixed(1)}`}
            >
              <div className={`w-2 h-2 rounded-full ${getScoreColor(value).dot}`} />
              <span className="text-[10px] text-white/30">{label}</span>
              <span className="text-[10px] font-mono text-white/45">{value.toFixed(1)}</span>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {entries.map(([key, label], i) => {
        const value = scores[key as keyof HookScores] ?? 0;
        return (
          <div key={key} className="flex items-center gap-2.5">
            <span className="text-[10px] text-white/35 w-16 text-right shrink-0 font-medium">
              {label}
            </span>
            <div className="flex-1 h-[5px] rounded-full bg-white/[0.04] overflow-hidden">
              <motion.div
                className={`h-full rounded-full bg-gradient-to-r ${getScoreColor(value).gradient}`}
                initial={{ width: "0%" }}
                animate={{ width: `${(value / 10) * 100}%` }}
                transition={{
                  type: "spring",
                  stiffness: 80,
                  damping: 20,
                  delay: i * 0.04,
                }}
              />
            </div>
            <span className="text-[10px] font-mono text-white/40 w-6 text-right tabular-nums">
              {value.toFixed(1)}
            </span>
          </div>
        );
      })}
    </div>
  );
});
