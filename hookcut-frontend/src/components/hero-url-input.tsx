"use client";

import { useState, useCallback, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import type { VideoMeta } from "@/lib/types";
import { NICHES, LANGUAGES } from "@/lib/constants";
import { formatDuration } from "@/lib/utils";
import { useAnalyze } from "@/contexts/analyze-context";

interface HeroUrlInputProps {
  light?: boolean;
}

const HeroUrlInput = memo(function HeroUrlInput({ light = false }: HeroUrlInputProps) {
  const onAnalyze = useAnalyze();
  const [url, setUrl] = useState("");
  const [validating, setValidating] = useState(false);
  const [videoMeta, setVideoMeta] = useState<VideoMeta | null>(null);
  const [error, setError] = useState("");
  const [niche, setNiche] = useState("Generic");
  const [language, setLanguage] = useState("English");

  const handleUrlChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
    setVideoMeta(null);
    setError("");
  }, []);

  const handleValidate = useCallback(async () => {
    const trimmed = url.trim();
    if (!trimmed) return;
    setValidating(true);
    setError("");
    setVideoMeta(null);
    try {
      const result = await api.validateUrl(trimmed);
      if (result.valid && result.video_id && result.title) {
        setVideoMeta({
          video_id: result.video_id,
          title: result.title,
          duration_seconds: result.duration_seconds ?? 0,
        });
      } else {
        setError(result.error ?? "Invalid YouTube URL");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Validation failed");
    } finally {
      setValidating(false);
    }
  }, [url]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") handleValidate();
    },
    [handleValidate]
  );

  const handleSubmit = useCallback(() => {
    if (!videoMeta) return;
    onAnalyze(url.trim(), niche, language, videoMeta);
  }, [url, niche, videoMeta, onAnalyze]);

  const borderBase = light
    ? "border-[#E4E4E7] bg-white focus-within:border-[#E84A2F]/50"
    : "border-white/[0.09] bg-white/[0.04] focus-within:border-[#E84A2F]/40 focus-within:bg-white/[0.06]";
  const textColor = light
    ? "text-[#111] placeholder:text-[#A1A1AA]"
    : "text-white/75 placeholder:text-white/25";
  const microColor = light ? "text-[#A1A1AA]" : "text-white/25";

  return (
    <div className="w-full">
      <div
        className={`flex items-center gap-2 border rounded-xl px-4 py-1 transition-all duration-300 shadow-sm ${borderBase}`}
      >
        <svg
          className="w-5 h-5 text-red-500 shrink-0"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
        </svg>
        <input
          type="text"
          value={url}
          onChange={handleUrlChange}
          onKeyDown={handleKeyDown}
          placeholder="Paste a YouTube URL..."
          className={`flex-1 bg-transparent outline-none py-3.5 text-base ${textColor}`}
          aria-label="YouTube URL"
        />
        <button
          onClick={handleValidate}
          disabled={validating || !url.trim()}
          className="shrink-0 px-5 py-2.5 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] disabled:opacity-40 transition-colors flex items-center gap-2"
        >
          {validating && (
            <svg
              className="w-4 h-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="3"
                strokeDasharray="30 70"
              />
            </svg>
          )}
          {validating ? "Checking…" : "Find My Hooks →"}
        </button>
      </div>

      {!videoMeta && !error && (
        <p className={`text-xs mt-3 text-center ${microColor}`}>
          120 free minutes · No credit card · Results in ~2 min
        </p>
      )}

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-3 text-sm text-red-400 text-center"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {videoMeta && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={`mt-4 p-4 rounded-xl border ${
              light ? "bg-white border-[#E4E4E7]" : "bg-white/[0.04] border-white/[0.08]"
            }`}
          >
            <p
              className={`text-sm font-medium line-clamp-1 mb-1 ${
                light ? "text-[#111]" : "text-white/80"
              }`}
            >
              {videoMeta.title}
            </p>
            <p className={`text-xs mb-4 ${light ? "text-[#71717A]" : "text-white/30"}`}>
              {formatDuration(videoMeta.duration_seconds)} ·{" "}
              ~{(videoMeta.duration_seconds / 60).toFixed(1)} credits
            </p>
            <div className="flex flex-wrap gap-1.5 mb-4">
              {NICHES.map((n) => (
                <button
                  key={n}
                  onClick={() => setNiche(n)}
                  className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
                    niche === n
                      ? "bg-[#E84A2F] text-white border-[#E84A2F]"
                      : light
                        ? "text-[#71717A] border-[#E4E4E7] hover:border-[#D4D4D8]"
                        : "text-white/40 border-white/[0.1] hover:border-white/20"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
            <div className="mb-4">
              <label
                htmlFor="language-select"
                className={`block text-xs font-medium mb-1.5 ${light ? "text-[#71717A]" : "text-white/40"}`}
              >
                Language
              </label>
              <select
                id="language-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className={`w-full px-3 py-2 rounded-lg border text-sm outline-none transition-colors ${
                  light
                    ? "bg-white border-[#E4E4E7] text-[#111] focus:border-[#E84A2F]/50"
                    : "bg-white/[0.04] border-white/[0.1] text-white/80 focus:border-[#E84A2F]/40"
                }`}
              >
                {LANGUAGES.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleSubmit}
              className="w-full py-3 rounded-xl bg-[#E84A2F] text-white font-semibold text-sm hover:bg-[#D13F25] transition-colors"
            >
              Start Analyzing →
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

export { HeroUrlInput };
export default HeroUrlInput;
