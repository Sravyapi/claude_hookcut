"use client";

import { useState, useEffect, useCallback, useRef, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { HeroUrlInput } from "@/components/hero-url-input";

// ── Demo data — multiple niches cycling ──────────────────────────────────────

type DemoVideo = {
  videoId: string;
  channel: string;
  initials: string;
  channelColor: string;
  title: string;
  duration: string;
  niche: string;
  hooks: {
    time: string;
    timePercent: number;
    label: string;
    score: number;
    color: string;
    caption: string;
  }[];
};

const DEMOS: DemoVideo[] = [
  {
    videoId: "v0oUvT4YiVM",
    channel: "BeerBiceps",
    initials: "BB",
    channelColor: "#E84A2F",
    title: "The Biggest Lesson Nobody Taught Me About Success",
    duration: "14:32",
    niche: "Podcast",
    hooks: [
      { time: "1:24", timePercent: 10, label: "Story Hook", score: 9.4, color: "#E84A2F", caption: "I was mass rejected from\nevery college I applied to." },
      { time: "4:51", timePercent: 33, label: "Curiosity Gap", score: 9.1, color: "#F59E0B", caption: "The biggest money mistake\nIndians in their 20s make." },
      { time: "7:18", timePercent: 50, label: "Pattern Interrupt", score: 9.6, color: "#3B82F6", caption: "What if everything you\nlearned was wrong?" },
      { time: "9:42", timePercent: 67, label: "Authority Play", score: 8.8, color: "#8B5CF6", caption: "I built a ₹200 crore\ncompany by age 27." },
      { time: "12:05", timePercent: 83, label: "Emotional Peak", score: 9.2, color: "#14B8A6", caption: "My parents didn't believe\nin me until this moment." },
    ],
  },
  {
    videoId: "nuE623i5HAc",
    channel: "warikoo",
    initials: "AW",
    channelColor: "#F59E0B",
    title: "How To Build Wealth In Your 20s (No One Tells You This)",
    duration: "18:07",
    niche: "Business",
    hooks: [
      { time: "0:42", timePercent: 4, label: "Contrarian Take", score: 9.3, color: "#F59E0B", caption: "Stop saving money.\nThat's the worst financial\nadvice you've ever heard." },
      { time: "3:15", timePercent: 18, label: "Data Shock", score: 8.9, color: "#E84A2F", caption: "97% of people who start\ninvesting in their 20s\nquit within 6 months." },
      { time: "6:30", timePercent: 36, label: "Story Hook", score: 9.5, color: "#3B82F6", caption: "At 25, I had ₹3 lakh\nin debt. Here's what\nI did differently." },
      { time: "10:48", timePercent: 60, label: "Framework Drop", score: 9.0, color: "#8B5CF6", caption: "The 70-20-10 rule that\nno finance guru will\never teach you." },
      { time: "15:22", timePercent: 85, label: "Call to Action", score: 8.7, color: "#14B8A6", caption: "Open this one app\nright now. Do it\nbefore this video ends." },
    ],
  },
  {
    videoId: "XHaKy1gnvQc",
    channel: "Dhruv Rathee",
    initials: "DR",
    channelColor: "#3B82F6",
    title: "The Dark Reality Behind India's Education System",
    duration: "22:15",
    niche: "Education",
    hooks: [
      { time: "0:18", timePercent: 1, label: "Pattern Interrupt", score: 9.7, color: "#3B82F6", caption: "What if I told you\neverything you learned\nin school was a lie?" },
      { time: "5:03", timePercent: 23, label: "Curiosity Gap", score: 9.2, color: "#F59E0B", caption: "This one policy change\ncould fix Indian education\novernight. But nobody wants it." },
      { time: "9:44", timePercent: 44, label: "Emotional Peak", score: 9.4, color: "#E84A2F", caption: "A 16-year-old student\nwrote this letter before\ntaking his own life." },
      { time: "14:30", timePercent: 65, label: "Data Shock", score: 8.9, color: "#8B5CF6", caption: "Finland has zero homework.\nTheir students outperform\nours in every metric." },
      { time: "19:12", timePercent: 86, label: "Authority Play", score: 9.1, color: "#14B8A6", caption: "I spoke to the education\nminister. His answer will\nshock you." },
    ],
  },
];

// How long each phase lasts (ms)
const PHASE_SCANNING = 1800;
const PHASE_HOOKS = 3500;
const PHASE_SHORT = 2500;
const PHASE_PAUSE = 800;

type Phase = "scanning" | "hooks" | "short" | "pause";

// ── Waveform bars (static, generated once) ───────────────────────────────────

const WAVEFORM_BARS = Array.from({ length: 80 }, (_, i) => {
  // Create a realistic-looking waveform pattern
  const base = Math.sin(i * 0.3) * 0.3 + 0.4;
  const noise = Math.sin(i * 1.7) * 0.15 + Math.cos(i * 2.3) * 0.1;
  return Math.max(0.1, Math.min(1, base + noise));
});

// ── ScoreRing ────────────────────────────────────────────────────────────────

const ScoreRing = memo(function ScoreRing({
  score,
  color,
  size = 44,
}: {
  score: number;
  color: string;
  size?: number;
}) {
  const r = (size - 6) / 2;
  const circ = 2 * Math.PI * r;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={3} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={3}
          strokeLinecap="round"
          strokeDasharray={`${(score / 10) * circ} ${circ}`}
          style={{ filter: `drop-shadow(0 0 4px ${color}60)` }}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-white tabular-nums">
        {score}
      </span>
    </div>
  );
});

// ── Main HeroSection ─────────────────────────────────────────────────────────

export function HeroSection() {
  const [active, setActive] = useState(false);
  const [demoIndex, setDemoIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>("scanning");
  const [scanProgress, setScanProgress] = useState(0);
  const [visibleHooks, setVisibleHooks] = useState(0);
  const [selectedHook, setSelectedHook] = useState(0);
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const scanRef = useRef<ReturnType<typeof requestAnimationFrame>>(undefined);
  const demoIndexRef = useRef(0);

  const handleActivate = useCallback(() => setActive(true), []);

  // Animation cycle
  useEffect(() => {
    if (active) return;

    let cancelled = false;

    function runCycle() {
      if (cancelled) return;

      // Phase 1: Scanning
      setDemoIndex(demoIndexRef.current);
      setPhase("scanning");
      setScanProgress(0);
      setVisibleHooks(0);
      setSelectedHook(0);

      const scanStart = performance.now();
      function animateScan() {
        if (cancelled) return;
        const elapsed = performance.now() - scanStart;
        const progress = Math.min(1, elapsed / PHASE_SCANNING);
        setScanProgress(progress);
        if (progress < 1) {
          scanRef.current = requestAnimationFrame(animateScan);
        }
      }
      scanRef.current = requestAnimationFrame(animateScan);

      // Phase 2: Hooks appear
      timerRef.current = setTimeout(() => {
        if (cancelled) return;
        setPhase("hooks");

        // Stagger hook appearance
        DEMOS[demoIndexRef.current].hooks.forEach((_, i) => {
          setTimeout(() => {
            if (cancelled) return;
            setVisibleHooks((prev) => Math.max(prev, i + 1));
          }, i * 400);
        });

        // Phase 3: Short extraction
        timerRef.current = setTimeout(() => {
          if (cancelled) return;
          setPhase("short");
          setSelectedHook(0);

          // Phase 4: Pause then restart
          timerRef.current = setTimeout(() => {
            if (cancelled) return;
            setPhase("pause");

            timerRef.current = setTimeout(() => {
              if (cancelled) return;
              // Advance to next demo
              demoIndexRef.current = (demoIndexRef.current + 1) % DEMOS.length;
              runCycle();
            }, PHASE_PAUSE);
          }, PHASE_SHORT);
        }, PHASE_HOOKS);
      }, PHASE_SCANNING);
    }

    runCycle();

    return () => {
      cancelled = true;
      clearTimeout(timerRef.current);
      if (scanRef.current) cancelAnimationFrame(scanRef.current);
    };
  }, [active]);

  const demo = DEMOS[demoIndex];
  const activeHook = demo.hooks[selectedHook];

  return (
    <section className="relative bg-[#0A0A0A] overflow-hidden px-6 pt-20 pb-12" aria-label="Hero">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div className="absolute inset-0 bg-grid" />
        <div
          className="absolute inset-0"
          style={{
            background: "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(232,74,47,0.05), transparent)",
          }}
        />
      </div>

      {/* ── Headline ── */}
      <div className="relative w-full max-w-3xl mx-auto text-center mb-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#E84A2F]/[0.1] border border-[#E84A2F]/20 text-[#E84A2F] text-xs font-semibold mb-7">
            <span className="w-1.5 h-1.5 rounded-full bg-[#E84A2F] animate-pulse" aria-hidden="true" />
            AI-powered hook detection
          </div>
          <h1 className="text-[clamp(36px,6.5vw,80px)] font-extrabold text-white leading-[1.05] tracking-[-0.04em] mb-5 font-[family-name:--font-display]">
            Find the hook.
            <br />
            <span className="text-[#E84A2F]">Stop the scroll.</span>
          </h1>
          <p className="text-white/40 text-lg leading-relaxed max-w-xl mx-auto">
            Paste a YouTube URL. AI finds the 5 moments most likely to go viral
            &mdash; scored, explained, and exported as ready-to-post Shorts.
          </p>
        </motion.div>
      </div>

      {/* ── Search bar ── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
        className="relative w-full max-w-3xl mx-auto mb-8"
      >
        {active ? (
          <HeroUrlInput />
        ) : (
          <button
            onClick={handleActivate}
            className="flex items-center gap-3 w-full rounded-2xl border border-white/[0.08] bg-white/[0.02] hover:border-white/[0.13] px-5 py-4 text-left transition-all duration-300 cursor-text"
            aria-label="Click to analyze your own YouTube video"
          >
            <svg className="w-4 h-4 shrink-0 text-[#FF0000]" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814z" />
            </svg>
            <span className="flex-1 text-sm font-mono text-white/30 truncate">
              Paste a YouTube URL to analyze&hellip;
            </span>
            <span className="text-xs px-3.5 py-1.5 rounded-full bg-[#E84A2F] text-white font-semibold shrink-0">
              Analyze &rarr;
            </span>
          </button>
        )}
      </motion.div>

      {/* ── Animated product demo ── */}
      {!active && (
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-5xl mx-auto"
        >
          {/* ── Unified demo container — video with floating Short overlay ── */}
          <div className="relative">
            {/* Video player mockup */}
            <div className="relative rounded-xl overflow-hidden border border-white/[0.06] bg-[#111]">
              {/* Thumbnail */}
              <div className="relative" style={{ aspectRatio: "2.2/1" }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`https://img.youtube.com/vi/${demo.videoId}/maxresdefault.jpg`}
                  alt=""
                  className="absolute inset-0 w-full h-full object-cover"
                  style={{ filter: "brightness(0.6) saturate(1.1)" }}
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = `https://img.youtube.com/vi/${demo.videoId}/hqdefault.jpg`;
                  }}
                />

                {/* Play button overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-12 h-12 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center border border-white/10">
                    <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </div>
                </div>

                {/* Video info bar */}
                <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent px-4 pb-2.5 pt-6">
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[7px] font-bold" style={{ background: demo.channelColor }}>
                      {demo.initials}
                    </div>
                    <div className="min-w-0">
                      <p className="text-white text-[11px] font-medium truncate">{demo.title}</p>
                      <p className="text-white/40 text-[9px]">{demo.channel} · {demo.duration}</p>
                    </div>
                  </div>
                </div>

                {/* Scanning overlay */}
                <AnimatePresence>
                  {phase === "scanning" && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0, transition: { duration: 0.5, ease: "easeInOut" } }}
                      className="absolute inset-0 bg-black/50 backdrop-blur-[2px] flex items-center justify-center"
                    >
                      <div className="w-72">
                        {/* Step label */}
                        <p className="text-white text-base font-semibold text-center mb-3">
                          {scanProgress < 0.4
                            ? "Extracting transcript..."
                            : scanProgress < 0.75
                              ? "Scoring hook moments..."
                              : "Ranking top 5 hooks..."}
                        </p>
                        {/* Progress bar */}
                        <div className="h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                          <div
                            className="h-full rounded-full bg-[#E84A2F]"
                            style={{
                              width: `${scanProgress * 100}%`,
                              boxShadow: "0 0 10px rgba(232, 74, 47, 0.6)",
                              transition: "width 0.05s linear",
                            }}
                          />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* ── Waveform timeline ── */}
              <div className="relative px-4 py-2.5 bg-[#0D0D0D]">
                <div className="flex items-end gap-[2px] h-6">
                  {WAVEFORM_BARS.map((height, i) => {
                    const barPercent = (i / WAVEFORM_BARS.length) * 100;
                    const isScanned = phase !== "scanning" || barPercent <= scanProgress * 100;
                    const isHookArea = demo.hooks.some(
                      (h) => Math.abs(h.timePercent - barPercent) < 4
                    );
                    const hookMatch =
                      (phase === "hooks" || phase === "short" || phase === "pause") &&
                      demo.hooks.find(
                        (h, idx) => Math.abs(h.timePercent - barPercent) < 2 && idx < visibleHooks
                      );

                    return (
                      <div
                        key={i}
                        className="flex-1 rounded-sm transition-all"
                        style={{
                          height: `${height * 100}%`,
                          minWidth: 2,
                          background: hookMatch
                            ? hookMatch.color
                            : isScanned
                              ? isHookArea && phase !== "scanning"
                                ? "rgba(232, 74, 47, 0.3)"
                                : "rgba(255, 255, 255, 0.15)"
                              : "rgba(255, 255, 255, 0.05)",
                          boxShadow: hookMatch ? `0 0 6px ${hookMatch.color}40` : "none",
                          transition: "background 0.3s, box-shadow 0.3s",
                        }}
                      />
                    );
                  })}
                </div>

                {/* Scan line */}
                {phase === "scanning" && (
                  <div
                    className="absolute top-1.5 bottom-1.5 w-[2px] bg-[#E84A2F] rounded-full pointer-events-none"
                    style={{
                      left: `${16 + scanProgress * (100 - 8)}%`,
                      boxShadow: "0 0 8px rgba(232, 74, 47, 0.6)",
                      transition: "left 0.05s linear",
                    }}
                  />
                )}

                {/* Hook markers */}
                {(phase === "hooks" || phase === "short" || phase === "pause") &&
                  demo.hooks.map(
                    (hook, i) =>
                      i < visibleHooks && (
                        <motion.button
                          key={i}
                          type="button"
                          initial={{ scale: 0, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          transition={{ type: "spring", stiffness: 500, damping: 25 }}
                          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
                          style={{ left: `${hook.timePercent}%` }}
                          onClick={() => setSelectedHook(i)}
                          aria-label={`Hook ${i + 1}: ${hook.label} at ${hook.time}`}
                        >
                          <div
                            className="w-3 h-3 rounded-full border-2 border-white/80 hook-pulse"
                            style={{
                              background: hook.color,
                              boxShadow: `0 0 8px ${hook.color}60`,
                            }}
                          />
                        </motion.button>
                      )
                  )}

                {/* Time labels */}
                <div className="flex justify-between mt-0.5">
                  <span className="text-[8px] text-white/20 font-mono">0:00</span>
                  <span className="text-[8px] text-white/20 font-mono">{demo.duration}</span>
                </div>
              </div>
            </div>

            {/* ── Hook pills (horizontal, compact) ── */}
            <AnimatePresence>
              {(phase === "hooks" || phase === "short" || phase === "pause") && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 4, transition: { duration: 0.4, ease: "easeInOut" } }}
                  transition={{ duration: 0.3 }}
                  className="mt-3 flex items-center gap-2 overflow-x-auto no-scrollbar px-1"
                >
                  <span className="text-white/30 text-[10px] font-semibold uppercase tracking-wider shrink-0">
                    {visibleHooks} hooks
                  </span>
                  {demo.hooks.map(
                    (hook, i) =>
                      i < visibleHooks && (
                        <motion.button
                          key={i}
                          type="button"
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: i * 0.06 }}
                          onClick={() => setSelectedHook(i)}
                          className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium transition-all duration-200 ${
                            selectedHook === i
                              ? "bg-white/[0.1] border border-white/[0.15] text-white"
                              : "bg-white/[0.03] border border-white/[0.06] text-white/50 hover:bg-white/[0.06]"
                          }`}
                        >
                          <div
                            className="w-1.5 h-1.5 rounded-full shrink-0"
                            style={{ background: hook.color }}
                          />
                          {hook.label}
                          <span className="text-[9px] font-mono text-white/30">{hook.score}</span>
                        </motion.button>
                      )
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* ── Floating Shorts (3 staggered phone frames) ── */}
            <AnimatePresence>
              {(phase === "short" || phase === "pause") && (
                <div className="absolute -bottom-2 right-2 lg:right-4 z-20 flex items-end gap-2 lg:gap-3">
                  {demo.hooks.slice(0, 3).map((hook, i) => (
                    <motion.div
                      key={`short-${i}`}
                      initial={{ opacity: 0, y: 30, scale: 0.85 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 12, scale: 0.95, transition: { duration: 0.5, ease: "easeInOut" } }}
                      transition={{
                        type: "spring",
                        stiffness: 300,
                        damping: 28,
                        delay: i * 0.12,
                      }}
                      className="relative"
                      style={{ width: i === 1 ? 120 : 100, marginBottom: i === 1 ? 8 : 0 }}
                    >
                      {/* Phone frame */}
                      <div
                        className="relative w-full rounded-[14px] lg:rounded-[16px] overflow-hidden"
                        style={{
                          aspectRatio: "9/16",
                          background: "#111",
                          border: `1px solid ${hook.color}${i === 1 ? "35" : "20"}`,
                          boxShadow: i === 1
                            ? `0 20px 60px rgba(0,0,0,0.7), 0 0 24px ${hook.color}15, 0 0 0 1px rgba(255,255,255,0.05)`
                            : "0 12px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.03)",
                        }}
                      >
                        {/* Thumbnail */}
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={`https://img.youtube.com/vi/${demo.videoId}/hqdefault.jpg`}
                          alt=""
                          className="absolute inset-0 w-full h-full object-cover"
                          style={{
                            objectPosition: `${30 + i * 20}% 20%`,
                            transform: "scale(1.4)",
                            filter: `brightness(${i === 1 ? 0.55 : 0.4}) saturate(1.15)`,
                          }}
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = "none";
                          }}
                        />

                        {/* Notch */}
                        <div className="absolute top-1.5 left-1/2 -translate-x-1/2 w-6 h-0.5 rounded-full bg-white/[0.06] z-10" />

                        {/* Score gauge (center card only for clarity) */}
                        {i === 1 && (
                          <div className="absolute top-4 right-1.5 z-10">
                            <ScoreRing score={hook.score} color={hook.color} size={28} />
                          </div>
                        )}

                        {/* Hook type badge */}
                        <div className="absolute top-4 left-1.5 z-10">
                          <div
                            className="px-1 py-0.5 rounded text-[6px] font-bold uppercase tracking-wider"
                            style={{
                              background: `${hook.color}25`,
                              border: `1px solid ${hook.color}30`,
                              color: hook.color,
                            }}
                          >
                            {hook.label}
                          </div>
                        </div>

                        {/* Caption */}
                        <div className="absolute inset-x-0 bottom-0 z-10 p-2">
                          <p
                            className="text-white font-bold text-[8px] leading-snug whitespace-pre-line line-clamp-3"
                            style={{ textShadow: "0 1px 6px rgba(0,0,0,0.9)" }}
                          >
                            {hook.caption}
                          </p>
                        </div>

                        {/* Bottom gradient */}
                        <div
                          className="absolute inset-x-0 bottom-0 pointer-events-none"
                          style={{
                            height: "60%",
                            background: "linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 50%, transparent 100%)",
                          }}
                        />
                      </div>
                    </motion.div>
                  ))}

                  {/* "3 Shorts ready" label */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, transition: { duration: 0.5, ease: "easeInOut" } }}
                    transition={{ delay: 0.4 }}
                    className="absolute -top-6 left-1/2 -translate-x-1/2 flex items-center gap-1.5 whitespace-nowrap"
                  >
                    <div className="w-1 h-1 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-white/50 text-[9px] font-semibold uppercase tracking-wider">
                      3 Shorts ready
                    </span>
                  </motion.div>
                </div>
              )}
            </AnimatePresence>
          </div>

          {/* ── Phase indicator + niche tabs (single row) ── */}
          <div className="flex items-center justify-between mt-6 gap-4">
            {/* Phase steps */}
            <div className="flex items-center gap-4">
              {[
                { key: "scanning", label: "Analyze", icon: "M21 21l-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607z" },
                { key: "hooks", label: "Find Hooks", icon: "M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" },
                { key: "short", label: "Export Short", icon: "M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" },
              ].map((step, i) => (
                <div key={step.key} className="flex items-center gap-2">
                  {i > 0 && <div className="w-4 h-px bg-white/[0.06]" />}
                  <div
                    className={`w-6 h-6 rounded-md flex items-center justify-center transition-all duration-500 ${
                      phase === step.key || (step.key === "scanning" && phase !== "scanning")
                        ? "bg-[#E84A2F]/15 border border-[#E84A2F]/25"
                        : "bg-white/[0.03] border border-white/[0.06]"
                    }`}
                  >
                    <svg
                      className={`w-3 h-3 transition-colors duration-500 ${
                        phase === step.key
                          ? "text-[#E84A2F]"
                          : (step.key === "scanning" && phase !== "scanning")
                            ? "text-[#E84A2F]/60"
                            : "text-white/20"
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={1.5}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d={step.icon} />
                    </svg>
                  </div>
                  <span
                    className={`text-[10px] font-medium transition-colors duration-500 hidden sm:inline ${
                      phase === step.key ? "text-white/70" : "text-white/20"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              ))}
            </div>

            {/* Niche tabs */}
            <div className="flex items-center gap-0.5">
              {DEMOS.map((d, i) => (
                <button
                  key={d.niche}
                  type="button"
                  className={`relative px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300 ${
                    demoIndex === i
                      ? "text-white bg-white/[0.07]"
                      : "text-white/25 hover:text-white/45"
                  }`}
                  aria-label={`${d.niche} demo`}
                  aria-disabled="true"
                >
                  {d.niche}
                  {demoIndex === i && (
                    <motion.div
                      layoutId="heroNicheTab"
                      className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full"
                      style={{ background: d.channelColor }}
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                    />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* CTA */}
          <div className="text-center mt-6">
            <button onClick={handleActivate} className="btn-primary px-8 py-3 rounded-full text-sm font-semibold">
              Try with your video &rarr;
            </button>
            <p className="text-white/25 text-xs mt-2.5">
              120 minutes free &middot; No credit card
            </p>
          </div>
        </motion.div>
      )}
    </section>
  );
}
