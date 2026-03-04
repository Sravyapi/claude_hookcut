"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fadeUp } from "../lib/motion";

interface ProgressStepProps {
  stage: string;
  progress: number;
  videoTitle: string;
  startTime: number;
}

const STEPS = [
  { label: "Fetching transcript", threshold: 10 },
  { label: "Analyzing hooks with AI", threshold: 40 },
  { label: "Validating results", threshold: 80 },
];

const FUN_MESSAGES = [
  "Scanning for scroll-stopping moments...",
  "Finding the hooks that make viewers stay...",
  "Identifying viral-worthy segments...",
  "Almost there, polishing results...",
];

export default function ProgressStep({
  stage,
  progress,
  videoTitle,
  startTime,
}: ProgressStepProps) {
  const [funMsgIdx, setFunMsgIdx] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setFunMsgIdx((i) => (i + 1) % FUN_MESSAGES.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!startTime) return;
    const tick = () => setElapsed(Math.floor((Date.now() - startTime) / 1000));
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [startTime]);

  return (
    <motion.div
      className="max-w-lg mx-auto text-center"
      variants={fadeUp}
      initial="hidden"
      animate="show"
    >
      {/* Animated concentric rings */}
      <div className="relative w-32 h-32 mx-auto mb-10">
        {/* Outer ring — conic gradient */}
        <div className="absolute inset-0 rounded-full orbit" style={{ animationDuration: "3s" }}>
          <svg className="w-full h-full" viewBox="0 0 128 128">
            <defs>
              <linearGradient id="ring-outer" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgba(139, 92, 246, 0.3)" />
                <stop offset="50%" stopColor="rgba(139, 92, 246, 0.05)" />
                <stop offset="100%" stopColor="rgba(139, 92, 246, 0.2)" />
              </linearGradient>
            </defs>
            <circle cx="64" cy="64" r="62" fill="none" stroke="url(#ring-outer)" strokeWidth="1.5" />
          </svg>
        </div>

        {/* Middle ring — reverse orbit */}
        <div className="absolute inset-3 rounded-full orbit-reverse">
          <svg className="w-full h-full" viewBox="0 0 104 104">
            <defs>
              <linearGradient id="ring-mid" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgba(139, 92, 246, 0.05)" />
                <stop offset="50%" stopColor="rgba(139, 92, 246, 0.25)" />
                <stop offset="100%" stopColor="rgba(139, 92, 246, 0.05)" />
              </linearGradient>
            </defs>
            <circle cx="52" cy="52" r="50" fill="none" stroke="url(#ring-mid)" strokeWidth="1" strokeDasharray="8 12" />
          </svg>
        </div>

        {/* Inner pulsing circle */}
        <div className="absolute inset-6 rounded-full bg-violet-500/8 pulse-glow" />

        {/* Center icon — morphs between states */}
        <div className="absolute inset-8 rounded-full bg-violet-500/10 flex items-center justify-center">
          <AnimatePresence mode="wait">
            {progress < 20 ? (
              <motion.svg
                key="transcript"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="w-8 h-8 text-violet-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </motion.svg>
            ) : progress < 70 ? (
              <motion.svg
                key="brain"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="w-8 h-8 text-violet-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </motion.svg>
            ) : (
              <motion.svg
                key="check"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="w-8 h-8 text-emerald-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </motion.svg>
            )}
          </AnimatePresence>
        </div>

        {/* Orbiting particles */}
        <div className="absolute inset-0 orbit" style={{ animationDuration: "2.5s" }}>
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.6)]" />
        </div>
        <div className="absolute inset-0 orbit" style={{ animationDuration: "3.5s", animationDelay: "-1s" }}>
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-purple-400/60 shadow-[0_0_6px_rgba(168,85,247,0.4)]" />
        </div>
      </div>

      <h2 className="text-2xl font-bold text-white/90 mb-2">
        Analyzing Video
      </h2>
      <p className="text-white/35 text-sm mb-1 truncate max-w-md mx-auto">
        {videoTitle}
      </p>

      {/* Rotating fun message */}
      <AnimatePresence mode="wait">
        <motion.p
          key={funMsgIdx}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.3 }}
          className="text-violet-400/80 text-sm font-medium mb-8 h-5"
        >
          {FUN_MESSAGES[funMsgIdx]}
        </motion.p>
      </AnimatePresence>

      {/* Segmented progress bar */}
      <div className="flex gap-1.5 mb-2">
        {STEPS.map((s, i) => {
          const segStart = i === 0 ? 0 : STEPS[i - 1].threshold;
          const segEnd = s.threshold;
          const segProgress = Math.max(0, Math.min(1, (progress - segStart) / (segEnd - segStart)));
          const isFull = progress >= segEnd;

          return (
            <div key={s.label} className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
              <motion.div
                className={`h-full rounded-full ${isFull ? "bg-gradient-to-r from-emerald-500 to-emerald-400" : "bg-gradient-to-r from-violet-600 via-purple-500 to-violet-400"}`}
                initial={{ width: "0%" }}
                animate={{ width: `${segProgress * 100}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex items-center justify-center gap-3">
        <p className="text-xs text-white/25 tabular-nums">{progress}%</p>
        {elapsed > 0 && (
          <p className="text-xs text-white/20 tabular-nums">
            {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")} elapsed
          </p>
        )}
      </div>

      {/* Horizontal stepper (desktop) */}
      <div className="mt-10 hidden sm:flex items-center justify-between max-w-sm mx-auto">
        {STEPS.map((s, i) => {
          const isDone = progress >= s.threshold;
          const isActive = !isDone && progress >= s.threshold - 20;
          const isLast = i === STEPS.length - 1;

          return (
            <div key={s.label} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center">
                <motion.div
                  className={`timeline-dot ${
                    isDone
                      ? "bg-emerald-500/15 border border-emerald-500/30"
                      : isActive
                        ? "bg-violet-500/15 border border-violet-500/30"
                        : "bg-white/3 border border-white/8"
                  }`}
                  animate={isActive ? { scale: [1, 1.08, 1] } : {}}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                >
                  {isDone ? (
                    <motion.svg
                      className="w-4 h-4 text-emerald-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </motion.svg>
                  ) : isActive ? (
                    <svg className="w-4 h-4 text-violet-400 spin" fill="none" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="30 70" />
                    </svg>
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-white/15" />
                  )}
                </motion.div>
                <span className={`text-[11px] mt-2 text-center leading-tight max-w-[80px] ${
                  isDone ? "text-white/60 font-medium" : isActive ? "text-violet-300 font-medium" : "text-white/20"
                }`}>
                  {s.label}
                </span>
              </div>
              {!isLast && (
                <div className={`stepper-line mx-2 mb-6 ${isDone ? "bg-emerald-500/20" : "bg-white/5"}`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Vertical stepper (mobile) */}
      <div className="mt-10 flex flex-col items-start max-w-xs mx-auto sm:hidden">
        {STEPS.map((s, i) => {
          const isDone = progress >= s.threshold;
          const isActive = !isDone && progress >= s.threshold - 20;
          const isLast = i === STEPS.length - 1;

          return (
            <div key={s.label}>
              <div className="flex items-center gap-4">
                <div className={`timeline-dot ${
                  isDone
                    ? "bg-emerald-500/15 border border-emerald-500/30"
                    : isActive
                      ? "bg-violet-500/15 border border-violet-500/30"
                      : "bg-white/3 border border-white/8"
                }`}>
                  {isDone ? (
                    <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : isActive ? (
                    <svg className="w-4 h-4 text-violet-400 spin" fill="none" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="30 70" />
                    </svg>
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-white/15" />
                  )}
                </div>
                <span className={`text-sm ${
                  isDone ? "text-white/60 font-medium" : isActive ? "text-violet-300 font-medium" : "text-white/20"
                }`}>
                  {s.label}
                </span>
              </div>
              {!isLast && (
                <div className={`timeline-line ${isDone ? "bg-emerald-500/20" : "bg-white/5"}`} />
              )}
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
