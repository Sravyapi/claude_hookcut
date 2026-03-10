"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { formatClipTime } from "@/lib/clip-utils";
import type { YTPlayerInstance } from "@/lib/types";

type TimelineScrubberProps = {
  duration: number;
  startTime: number;
  endTime: number;
  onStartChange: (time: number) => void;
  onEndChange: (time: number) => void;
  player?: YTPlayerInstance;
};

export function TimelineScrubber({
  duration,
  startTime,
  endTime,
  onStartChange,
  onEndChange,
  player,
}: TimelineScrubberProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState<"start" | "end" | null>(null);
  const [playbackPosition, setPlaybackPosition] = useState(0);
  const rafRef = useRef<number>(0);

  // Poll playback position at ~15fps
  useEffect(() => {
    if (!player) return;

    let lastTime = 0;
    const throttledPoll = () => {
      const now = performance.now();
      if (now - lastTime >= 66) {
        try {
          const t = player.getCurrentTime?.();
          if (typeof t === "number") setPlaybackPosition(t);
        } catch (err) {
          console.warn("Failed to get playback position:", err);
        }
        lastTime = now;
      }
      rafRef.current = requestAnimationFrame(throttledPoll);
    };

    rafRef.current = requestAnimationFrame(throttledPoll);
    return () => cancelAnimationFrame(rafRef.current);
  }, [player]);

  const getTimeFromX = useCallback((clientX: number): number => {
    if (!trackRef.current) return 0;
    const rect = trackRef.current.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    return pct * duration;
  }, [duration]);

  const handlePointerDown = useCallback((handle: "start" | "end") => (e: React.PointerEvent) => {
    e.preventDefault();
    setDragging(handle);
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragging) return;
    const time = getTimeFromX(e.clientX);
    if (dragging === "start") {
      onStartChange(Math.min(time, endTime - 3));
    } else {
      onEndChange(Math.max(time, startTime + 3));
    }
  }, [dragging, getTimeFromX, startTime, endTime, onStartChange, onEndChange]);

  const handlePointerUp = useCallback(() => {
    setDragging(null);
  }, []);

  const handleTrackClick = useCallback((e: React.MouseEvent) => {
    if (dragging) return;
    const time = getTimeFromX(e.clientX);
    if (player?.seekTo) {
      player.seekTo(time, true);
    }
  }, [dragging, getTimeFromX, player]);

  const startPct = duration > 0 ? (startTime / duration) * 100 : 0;
  const endPct = duration > 0 ? (endTime / duration) * 100 : 0;
  const needlePct = duration > 0 ? (playbackPosition / duration) * 100 : 0;

  return (
    <div className="select-none">
      <div
        ref={trackRef}
        className="relative h-8 rounded-full bg-white/10 cursor-pointer"
        onClick={handleTrackClick}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        {/* Selected range */}
        <div
          className="absolute top-1 bottom-1 rounded-full bg-gradient-to-r from-violet-500 to-cyan-500 opacity-60"
          style={{ left: `${startPct}%`, width: `${endPct - startPct}%` }}
        />

        {/* Playback needle */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white z-10 pointer-events-none"
          style={{ left: `${needlePct}%` }}
        />

        {/* Start handle */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-white/80 backdrop-blur border-2 border-violet-400 cursor-grab active:cursor-grabbing z-20 shadow-lg shadow-violet-500/20"
          style={{ left: `calc(${startPct}% - 10px)` }}
          onPointerDown={handlePointerDown("start")}
          tabIndex={0}
          role="slider"
          aria-label="Clip start time"
          aria-valuemin={0}
          aria-valuemax={duration}
          aria-valuenow={startTime}
          onKeyDown={e => {
            if (e.key === "ArrowRight") onStartChange(Math.min(startTime + (e.shiftKey ? 5 : 1), endTime - 3));
            if (e.key === "ArrowLeft") onStartChange(Math.max(startTime - (e.shiftKey ? 5 : 1), 0));
          }}
        >
          {dragging === "start" && (
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded bg-black/80 text-xs text-white whitespace-nowrap">
              {formatClipTime(startTime)}
            </div>
          )}
        </div>

        {/* End handle */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-white/80 backdrop-blur border-2 border-cyan-400 cursor-grab active:cursor-grabbing z-20 shadow-lg shadow-cyan-500/20"
          style={{ left: `calc(${endPct}% - 10px)` }}
          onPointerDown={handlePointerDown("end")}
          tabIndex={0}
          role="slider"
          aria-label="Clip end time"
          aria-valuemin={0}
          aria-valuemax={duration}
          aria-valuenow={endTime}
          onKeyDown={e => {
            if (e.key === "ArrowRight") onEndChange(Math.min(endTime + (e.shiftKey ? 5 : 1), duration));
            if (e.key === "ArrowLeft") onEndChange(Math.max(endTime - (e.shiftKey ? 5 : 1), startTime + 3));
          }}
        >
          {dragging === "end" && (
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded bg-black/80 text-xs text-white whitespace-nowrap">
              {formatClipTime(endTime)}
            </div>
          )}
        </div>
      </div>

      {/* Duration labels */}
      <div className="flex justify-between mt-1 text-xs text-white/40">
        <span>0:00</span>
        <span>{formatClipTime(duration)}</span>
      </div>
    </div>
  );
}
