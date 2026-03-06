"use client";

import { memo, useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import ShortCard from "./short-card";

interface ShortsStepProps {
  shortIds: string[];
  onReset: () => void;
}

export const ShortsStep = memo(function ShortsStep({ shortIds, onReset }: ShortsStepProps) {
  const handleReset = useCallback(() => onReset(), [onReset]);
  const startRef = useRef(Date.now());
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const elapsedFormatted = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, "0")}`;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <motion.div
        className="text-center mb-10"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[--color-primary]/8 border border-[--color-primary]/15 text-[--color-primary] text-xs font-medium mb-5">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Generating {shortIds.length} {shortIds.length === 1 ? "Short" : "Shorts"}
        </div>

        <h2 className="text-3xl font-bold text-white/90 mb-2">Your Shorts</h2>
        <p className="text-[--color-muted] text-sm">
          Each Short is being rendered in 9:16 format with captions
        </p>

        {/* Elapsed clock */}
        <div className="inline-flex items-center gap-1.5 mt-3 text-[11px] text-white/25 font-mono">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="tabular-nums">{elapsedFormatted} elapsed</span>
        </div>
      </motion.div>

      {/* Cards — horizontal scroll on desktop, vertical on mobile */}
      <div
        className={`flex gap-4 mb-10 ${
          shortIds.length > 1
            ? "flex-col sm:flex-row sm:overflow-x-auto sm:snap-x no-scrollbar sm:pb-4 sm:gap-5"
            : "justify-center"
        }`}
      >
        {shortIds.map((id, i) => (
          <div
            key={id}
            className={`${
              shortIds.length > 1 ? "sm:snap-start sm:shrink-0 sm:w-[280px]" : "sm:w-[300px]"
            } w-full`}
          >
            <ShortCard shortId={id} index={i} />
          </div>
        ))}
      </div>

      {/* Reset button */}
      <motion.div
        className="text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <button
          onClick={handleReset}
          className="btn-secondary text-sm inline-flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Analyze Another Video
        </button>
      </motion.div>
    </div>
  );
});

export default ShortsStep;
