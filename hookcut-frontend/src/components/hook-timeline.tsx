"use client";

import { memo, useMemo } from "react";
import { motion } from "framer-motion";
import { getScoreColor } from "@/lib/utils";

export interface TimelineHook {
  id: string;
  start_time: string;
  attention_score: number;
  rank: number;
}

interface HookTimelineProps {
  hooks: TimelineHook[];
  /** Total video duration in seconds — used to compute marker positions */
  durationSeconds: number;
  /** ID of the currently hovered hook card — triggers pulse on matching marker */
  activeHookId?: string | null;
  onMarkerClick?: (id: string) => void;
  className?: string;
}

/** Parses "M:SS" or "H:MM:SS" → seconds */
function parseTimestamp(ts: string): number {
  const parts = ts.split(":").map(Number);
  if (parts.length === 2) return (parts[0] ?? 0) * 60 + (parts[1] ?? 0);
  if (parts.length === 3) return (parts[0] ?? 0) * 3600 + (parts[1] ?? 0) * 60 + (parts[2] ?? 0);
  return 0;
}

/** SVG hook-marker timeline. Used in hooks-step and marketing homepage. */
export const HookTimeline = memo(function HookTimeline({
  hooks,
  durationSeconds,
  activeHookId,
  onMarkerClick,
  className = "",
}: HookTimelineProps) {
  const safeHooks = useMemo(
    () => hooks.filter((h) => h.start_time && h.attention_score >= 0),
    [hooks]
  );

  if (safeHooks.length === 0) return null;

  const trackHeight = 48;
  const markerY = 28;
  const tickH = 10;
  const labelY = markerY + tickH + 14;
  const svgHeight = labelY + 14;

  return (
    <div className={`w-full overflow-hidden ${className}`} role="img" aria-label="Hook timeline">
      <svg
        viewBox={`0 0 1000 ${svgHeight}`}
        preserveAspectRatio="none"
        width="100%"
        height={trackHeight + 20}
        aria-hidden="true"
      >
        {/* Track */}
        <line
          x1="0"
          y1={markerY}
          x2="1000"
          y2={markerY}
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="1.5"
        />
        {/* Start / end ticks */}
        <line x1="0" y1={markerY - 4} x2="0" y2={markerY + 4} stroke="rgba(255,255,255,0.12)" strokeWidth="1.5" />
        <line x1="1000" y1={markerY - 4} x2="1000" y2={markerY + 4} stroke="rgba(255,255,255,0.12)" strokeWidth="1.5" />

        {safeHooks.map((hook) => {
          const seconds = parseTimestamp(hook.start_time);
          const xPct = durationSeconds > 0 ? seconds / durationSeconds : 0;
          const x = Math.max(0, Math.min(1, xPct)) * 1000;
          const { hex } = getScoreColor(hook.attention_score);
          const isActive = activeHookId === hook.id;

          return (
            <g
              key={hook.id}
              role={onMarkerClick ? "button" : undefined}
              tabIndex={onMarkerClick ? 0 : undefined}
              aria-label={`Hook ${hook.rank} at ${hook.start_time}`}
              onClick={() => onMarkerClick?.(hook.id)}
              onKeyDown={(e) => {
                if ((e.key === "Enter" || e.key === " ") && onMarkerClick) {
                  onMarkerClick(hook.id);
                }
              }}
              style={{ cursor: onMarkerClick ? "pointer" : "default" }}
            >
              {/* Glow ring when active */}
              {isActive && (
                <motion.circle
                  cx={x}
                  cy={markerY}
                  r={10}
                  fill="none"
                  stroke={hex}
                  strokeWidth="2"
                  initial={{ opacity: 0, r: 6 }}
                  animate={{ opacity: [0.6, 0], r: [8, 16] }}
                  transition={{ duration: 1.2, repeat: Infinity, ease: "easeOut" }}
                />
              )}
              {/* Tick line */}
              <line
                x1={x}
                y1={markerY - tickH / 2}
                x2={x}
                y2={markerY + tickH / 2}
                stroke={hex}
                strokeWidth={isActive ? 2 : 1.5}
                opacity={isActive ? 1 : 0.7}
              />
              {/* Triangle marker above track */}
              <motion.polygon
                points={`${x},${markerY - tickH} ${x - 5},${markerY - tickH - 8} ${x + 5},${markerY - tickH - 8}`}
                fill={hex}
                opacity={isActive ? 1 : 0.75}
                animate={isActive ? { opacity: [0.75, 1, 0.75] } : { opacity: 0.75 }}
                transition={{ duration: 1.2, repeat: isActive ? Infinity : 0 }}
              />
              {/* Timestamp label below track */}
              <text
                x={x}
                y={labelY}
                textAnchor="middle"
                fontSize="11"
                fontFamily="var(--font-mono, monospace)"
                fill={isActive ? hex : "rgba(255,255,255,0.3)"}
                fontWeight={isActive ? "600" : "400"}
              >
                {hook.start_time}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
});
