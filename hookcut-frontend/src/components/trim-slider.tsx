"use client";

import { useCallback } from "react";

interface TrimSliderProps {
  startSeconds: number;
  endSeconds: number;
  originalStart: number;
  originalEnd: number;
  onChange: (start: number, end: number) => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function parseTimestamp(ts: string): number {
  // Handles "M:SS" or "MM:SS" or composite "M:SS+M:SS"
  const first = ts.split("+")[0].trim();
  const parts = first.split(":");
  if (parts.length === 2) {
    return parseInt(parts[0], 10) * 60 + parseFloat(parts[1]);
  }
  return parseFloat(first) || 0;
}

export default function TrimSlider({
  startSeconds,
  endSeconds,
  originalStart,
  originalEnd,
  onChange,
}: TrimSliderProps) {
  const minStart = Math.max(0, originalStart - 10);
  const maxStart = endSeconds - 5;
  const minEnd = startSeconds + 5;
  const maxEnd = originalEnd + 10;

  const adjustStart = useCallback(
    (delta: number) => {
      const next = Math.max(minStart, Math.min(maxStart, startSeconds + delta));
      onChange(Math.round(next * 10) / 10, endSeconds);
    },
    [startSeconds, endSeconds, minStart, maxStart, onChange]
  );

  const adjustEnd = useCallback(
    (delta: number) => {
      const next = Math.max(minEnd, Math.min(maxEnd, endSeconds + delta));
      onChange(startSeconds, Math.round(next * 10) / 10);
    },
    [startSeconds, endSeconds, minEnd, maxEnd, onChange]
  );

  const duration = endSeconds - startSeconds;
  const isModified =
    Math.abs(startSeconds - originalStart) > 0.1 ||
    Math.abs(endSeconds - originalEnd) > 0.1;

  return (
    <div
      className="flex items-center gap-3 text-xs"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Start control */}
      <div className="flex items-center gap-1">
        <span className="text-white/25 w-8">Start</span>
        <button
          onClick={() => adjustStart(-1)}
          disabled={startSeconds <= minStart}
          className="w-6 h-6 rounded-md bg-white/[0.04] border border-white/[0.08] text-white/50 hover:text-white/80 hover:bg-white/[0.08] disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          aria-label="Decrease start time"
        >
          -
        </button>
        <span className="tabular-nums text-white/60 w-10 text-center font-medium">
          {formatTime(startSeconds)}
        </span>
        <button
          onClick={() => adjustStart(1)}
          disabled={startSeconds >= maxStart}
          className="w-6 h-6 rounded-md bg-white/[0.04] border border-white/[0.08] text-white/50 hover:text-white/80 hover:bg-white/[0.08] disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          aria-label="Increase start time"
        >
          +
        </button>
      </div>

      {/* Duration badge */}
      <span
        className={`tabular-nums px-2 py-0.5 rounded-full text-[10px] ${
          isModified
            ? "bg-violet-500/15 text-violet-300 border border-violet-500/20"
            : "bg-white/[0.04] text-white/30 border border-white/[0.06]"
        }`}
      >
        {duration.toFixed(0)}s
      </span>

      {/* End control */}
      <div className="flex items-center gap-1">
        <span className="text-white/25 w-6">End</span>
        <button
          onClick={() => adjustEnd(-1)}
          disabled={endSeconds <= minEnd}
          className="w-6 h-6 rounded-md bg-white/[0.04] border border-white/[0.08] text-white/50 hover:text-white/80 hover:bg-white/[0.08] disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          aria-label="Decrease end time"
        >
          -
        </button>
        <span className="tabular-nums text-white/60 w-10 text-center font-medium">
          {formatTime(endSeconds)}
        </span>
        <button
          onClick={() => adjustEnd(1)}
          disabled={endSeconds >= maxEnd}
          className="w-6 h-6 rounded-md bg-white/[0.04] border border-white/[0.08] text-white/50 hover:text-white/80 hover:bg-white/[0.08] disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          aria-label="Increase end time"
        >
          +
        </button>
      </div>

      {/* Modified indicator */}
      {isModified && (
        <span className="text-[10px] text-violet-400/60">trimmed</span>
      )}
    </div>
  );
}
