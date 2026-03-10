"use client";

import { memo, useRef, useCallback } from "react";
import { ClipShortCard } from "./clip-preview";

interface GeneratingStepProps {
  shortIds: string[];
  onAllDone: () => void;
  isComplete: boolean;
  onReset: () => void;
}

export const GeneratingStep = memo(function GeneratingStep({
  shortIds,
  onAllDone,
  isComplete,
  onReset,
}: GeneratingStepProps) {
  const doneCountRef = useRef(0);
  const firedRef = useRef(false);

  const handleShortDone = useCallback(() => {
    doneCountRef.current += 1;
    if (doneCountRef.current >= shortIds.length && !firedRef.current) {
      firedRef.current = true;
      onAllDone();
    }
  }, [shortIds.length, onAllDone]);

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 rounded-2xl text-center">
        <h3 className="text-lg font-semibold text-white mb-2">
          {isComplete ? "Clips Ready!" : "Generating Clips..."}
        </h3>
        <p className="text-sm text-white/50 mb-6">
          {isComplete
            ? "Your clips are ready to download"
            : `Processing ${shortIds.length} clip${shortIds.length !== 1 ? "s" : ""}...`}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {shortIds.map((shortId, i) => (
            <ClipShortCard
              key={shortId}
              shortId={shortId}
              index={i}
              onDone={handleShortDone}
            />
          ))}
        </div>

        <button
          onClick={onReset}
          className="mt-6 px-6 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 text-sm border border-white/10 transition-colors"
        >
          Clip Another Video
        </button>
      </div>
    </div>
  );
});
