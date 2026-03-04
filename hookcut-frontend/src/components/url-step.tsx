"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform } from "framer-motion";
import { api } from "../lib/api";
import type { VideoMeta } from "../lib/types";
import { DEFAULT_NICHE, DEFAULT_LANGUAGE } from "../lib/types";
import { NICHES } from "../lib/constants";
import { formatDuration, youtubeThumbUrl } from "../lib/utils";
import { fadeUp, scaleIn, staggerContainer, fadeUpItem } from "../lib/motion";

interface UrlStepProps {
  onAnalyze: (
    url: string,
    niche: string,
    language: string,
    meta: VideoMeta
  ) => void;
}

const PLACEHOLDER_URLS = [
  "Paste any YouTube URL...",
  "https://youtube.com/watch?v=...",
  "Works with podcasts, tutorials, vlogs...",
  "Any video up to 2 hours long...",
];

export default function UrlStep({ onAnalyze }: UrlStepProps) {
  const [url, setUrl] = useState("");
  const [validating, setValidating] = useState(false);
  const [videoMeta, setVideoMeta] = useState<VideoMeta | null>(null);
  const [error, setError] = useState("");
  const [niche, setNiche] = useState(DEFAULT_NICHE);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const heroRef = useRef<HTMLDivElement>(null);

  // Mouse-tracked parallax for background orbs
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const orbX = useTransform(mouseX, [-400, 400], [-15, 15]);
  const orbY = useTransform(mouseY, [-400, 400], [-15, 15]);

  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      const rect = heroRef.current?.getBoundingClientRect();
      if (!rect) return;
      mouseX.set(e.clientX - rect.left - rect.width / 2);
      mouseY.set(e.clientY - rect.top - rect.height / 2);
    };
    window.addEventListener("mousemove", handleMouse);
    return () => window.removeEventListener("mousemove", handleMouse);
  }, [mouseX, mouseY]);

  // Typewriter placeholder cycling
  useEffect(() => {
    if (url) return;
    const timer = setInterval(() => {
      setPlaceholderIdx((i) => (i + 1) % PLACEHOLDER_URLS.length);
    }, 3000);
    return () => clearInterval(timer);
  }, [url]);

  const handleValidate = async () => {
    if (!url.trim()) return;
    setValidating(true);
    setError("");
    setVideoMeta(null);

    try {
      const result = await api.validateUrl(url.trim());
      if (result.valid && result.video_id && result.title) {
        setVideoMeta({
          video_id: result.video_id,
          title: result.title,
          duration_seconds: result.duration_seconds || 0,
        });
      } else {
        setError(result.error || "Invalid YouTube URL");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setValidating(false);
    }
  };

  const handleSubmit = () => {
    if (!videoMeta) return;
    onAnalyze(url.trim(), niche, DEFAULT_LANGUAGE, videoMeta);
  };

  const isReady = !!videoMeta;

  return (
    <div ref={heroRef} className="relative">
      {/* Background: grid + parallax orbs */}
      <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-grid opacity-40" />
        <motion.div
          style={{ x: orbX, y: orbY }}
          className="absolute top-[-10%] left-[10%] w-80 h-80 rounded-full bg-violet-500/[0.05] blur-[100px] float-slow"
        />
        <motion.div
          style={{ x: useTransform(orbX, (v) => -v * 0.7), y: useTransform(orbY, (v) => -v * 0.7) }}
          className="absolute bottom-[-10%] right-[12%] w-72 h-72 rounded-full bg-blue-500/[0.04] blur-[90px] float-slower"
        />
        <div className="absolute top-[40%] right-[5%] w-56 h-56 rounded-full bg-purple-500/[0.03] blur-[70px] float-slow" style={{ animationDelay: "-7s" }} />
      </div>

      {/* Hero text */}
      <motion.div
        className="text-center mb-14"
        variants={staggerContainer}
        initial="hidden"
        animate="show"
      >
        <motion.div variants={fadeUpItem}>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-violet-500/20 bg-violet-500/5 text-violet-300 text-xs font-medium mb-7">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-400" />
            </span>
            AI-Powered Hook Extraction
          </div>
        </motion.div>

        <motion.h1
          variants={fadeUpItem}
          className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-[-0.02em] mb-6 leading-[1.05]"
        >
          <span className="text-white/95">1 YouTube Video</span>
          <br />
          <span className="gradient-text-animated">10 Viral Shorts</span>
        </motion.h1>

        <motion.p
          variants={fadeUpItem}
          className="text-white/35 text-lg sm:text-xl max-w-xl mx-auto leading-relaxed"
        >
          AI extracts the most engaging hook segments and renders
          them as scroll-stopping Shorts
        </motion.p>
      </motion.div>

      {/* URL Input */}
      <motion.div
        className="max-w-2xl mx-auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, type: "spring", stiffness: 200, damping: 24 }}
      >
        <div className="glass rounded-2xl p-2.5 flex items-center gap-2 transition-all duration-300 focus-within:border-violet-500/30 focus-within:shadow-[0_0_40px_rgba(139,92,246,0.1)] gradient-border">
          <div className="flex-1 flex items-center gap-3 px-4">
            <svg
              className="w-5 h-5 text-red-400/80 shrink-0"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
            </svg>
            <input
              type="text"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setVideoMeta(null);
                setError("");
              }}
              onKeyDown={(e) => e.key === "Enter" && handleValidate()}
              placeholder={PLACEHOLDER_URLS[placeholderIdx]}
              className="flex-1 bg-transparent outline-none text-white placeholder:text-white/20 py-3.5 text-base"
            />
          </div>
          <button
            onClick={handleValidate}
            disabled={validating || !url.trim()}
            className="btn-primary flex items-center gap-2 text-sm shrink-0"
          >
            {validating ? (
              <>
                <svg className="w-4 h-4 spin" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="30 70" />
                </svg>
                Checking...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Validate
              </>
            )}
          </button>
        </div>

        {/* Social proof strip */}
        {!videoMeta && !error && (
          <motion.div
            className="flex items-center justify-center gap-3 mt-5"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <div className="flex -space-x-2">
              {[
                "bg-gradient-to-br from-violet-400 to-purple-600",
                "bg-gradient-to-br from-blue-400 to-cyan-600",
                "bg-gradient-to-br from-emerald-400 to-green-600",
                "bg-gradient-to-br from-amber-400 to-orange-600",
              ].map((bg, i) => (
                <div
                  key={i}
                  className={`w-7 h-7 rounded-full ${bg} border-2 border-[#06060e] flex items-center justify-center text-[9px] font-bold text-white/80`}
                >
                  {["S", "A", "M", "R"][i]}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-1.5">
              <div className="flex gap-0.5">
                {[1, 2, 3, 4, 5].map((s) => (
                  <svg key={s} className="w-3.5 h-3.5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
              <span className="text-xs text-white/25">Trusted by 1,000+ creators</span>
            </div>
          </motion.div>
        )}

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="mt-4 p-4 rounded-xl bg-red-500/8 border border-red-500/15 text-red-400 text-sm flex items-start gap-3"
            >
              <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Video meta + config */}
        <AnimatePresence>
          {videoMeta && (
            <motion.div
              className="mt-6"
              variants={scaleIn}
              initial="hidden"
              animate="show"
              exit="hidden"
            >
              {/* Video preview card */}
              <div className="glass-card rounded-2xl p-5 mb-6 gradient-border">
                <div className="flex items-start gap-5">
                  <div className="w-48 h-28 rounded-xl bg-white/5 overflow-hidden shrink-0 shadow-lg relative group">
                    <img
                      src={youtubeThumbUrl(videoMeta.video_id)}
                      alt={videoMeta.title}
                      className="w-full h-full object-cover"
                    />
                    {/* Play button overlay */}
                    <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                        <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </div>
                    </div>
                    {/* Duration badge */}
                    <div className="absolute bottom-1.5 right-1.5 px-1.5 py-0.5 rounded bg-black/70 text-[10px] text-white font-medium">
                      {formatDuration(videoMeta.duration_seconds)}
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-white/90 leading-snug line-clamp-2 text-[15px]">
                      {videoMeta.title}
                    </h3>
                    <div className="flex items-center gap-3 mt-3">
                      <span className="inline-flex items-center gap-1.5 text-xs text-white/40">
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {formatDuration(videoMeta.duration_seconds)}
                      </span>
                      <span className="w-1 h-1 rounded-full bg-white/15" />
                      <span className="text-xs text-violet-400/60">
                        ~{(videoMeta.duration_seconds / 60).toFixed(1)} min credits
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Niche selector — animated pills */}
              <motion.div
                className="mb-6"
                variants={staggerContainer}
                initial="hidden"
                animate="show"
              >
                <label className="text-xs text-white/35 uppercase tracking-wider mb-3 block font-medium">
                  Content Niche
                </label>
                <div className="flex flex-wrap gap-2">
                  {NICHES.map((n) => (
                    <motion.button
                      key={n}
                      variants={fadeUpItem}
                      whileHover={{ scale: 1.04 }}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => setNiche(n)}
                      className={`niche-chip ${niche === n ? "active" : ""}`}
                    >
                      {n}
                    </motion.button>
                  ))}
                </div>
              </motion.div>

              {/* Language support note */}
              <div className="flex items-center gap-2.5 mb-8 px-1">
                <svg
                  className="w-4 h-4 text-violet-400/50 shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
                  />
                </svg>
                <span className="text-xs text-white/25">
                  Supports 12+ languages — auto-detected from transcript
                </span>
              </div>

              {/* Analyze button */}
              <motion.button
                onClick={handleSubmit}
                className={`btn-primary w-full text-center text-base py-4 flex items-center justify-center gap-3 ${isReady ? "pulse-glow" : ""}`}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Generate Hook Segments
                <motion.svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  initial={{ x: 0 }}
                  whileHover={{ x: 3 }}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </motion.svg>
              </motion.button>
              <p className="text-center text-xs text-white/20 mt-3">
                ~{(videoMeta.duration_seconds / 60).toFixed(1)} credits will be deducted
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
