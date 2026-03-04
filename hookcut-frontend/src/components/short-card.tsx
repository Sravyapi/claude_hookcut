"use client";

import { useState, useRef, memo } from "react";
import { motion } from "framer-motion";
import { api } from "../lib/api";
import { SHORT_STATUS } from "../lib/types";
import { useShortPoller } from "../hooks/useShortPoller";
import { formatDuration, formatFileSize } from "../lib/utils";

const STAGE_PROGRESS: Record<string, { pct: number; label: string }> = {
  queued: { pct: 5, label: "In queue..." },
  downloading: { pct: 35, label: "Downloading segment..." },
  processing: { pct: 65, label: "Rendering video..." },
  uploading: { pct: 85, label: "Uploading..." },
};

const CONFETTI = [
  { id: 0, angle: 0, r: 52, color: "#a78bfa" },
  { id: 1, angle: 30, r: 42, color: "#34d399" },
  { id: 2, angle: 60, r: 58, color: "#f472b6" },
  { id: 3, angle: 90, r: 44, color: "#60a5fa" },
  { id: 4, angle: 120, r: 54, color: "#facc15" },
  { id: 5, angle: 150, r: 40, color: "#a78bfa" },
  { id: 6, angle: 180, r: 50, color: "#34d399" },
  { id: 7, angle: 210, r: 46, color: "#f472b6" },
  { id: 8, angle: 240, r: 56, color: "#60a5fa" },
  { id: 9, angle: 270, r: 38, color: "#facc15" },
  { id: 10, angle: 300, r: 52, color: "#a78bfa" },
  { id: 11, angle: 330, r: 44, color: "#34d399" },
];

function ConfettiBurst() {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      {CONFETTI.map(({ id, angle, r, color }) => (
        <motion.div
          key={id}
          className="absolute w-2 h-2 rounded-full"
          style={{ backgroundColor: color }}
          initial={{ x: 0, y: 0, opacity: 0, scale: 0 }}
          animate={{
            x: Math.cos((angle * Math.PI) / 180) * r,
            y: Math.sin((angle * Math.PI) / 180) * r,
            opacity: [0, 1, 0],
            scale: [0, 1.2, 0.8],
          }}
          transition={{ duration: 0.9, ease: "easeOut", delay: 0.1 }}
        />
      ))}
    </div>
  );
}

function Waveform() {
  const heights = [0.55, 0.9, 0.65, 1.0, 0.75, 0.9, 0.6];
  return (
    <div className="flex items-center justify-center gap-1">
      {heights.map((h, i) => (
        <motion.div
          key={i}
          className="w-1.5 rounded-full bg-violet-400/70"
          animate={{ scaleY: [h, 0.25, h] }}
          transition={{
            duration: 0.85,
            repeat: Infinity,
            delay: i * 0.11,
            ease: "easeInOut",
          }}
          style={{ height: 36 }}
        />
      ))}
    </div>
  );
}

function PhoneStatusBar() {
  return (
    <div className="absolute top-0 inset-x-0 h-7 flex items-center justify-between px-2.5 bg-gradient-to-b from-black/60 to-transparent z-10">
      <span className="text-[9px] text-white/50 font-semibold tabular-nums">9:41</span>
      <div className="flex items-center gap-1">
        <div className="flex items-end gap-px" style={{ height: 10 }}>
          {[40, 60, 80, 100].map((h, i) => (
            <div
              key={i}
              className="w-0.5 bg-white/40 rounded-sm"
              style={{ height: `${h}%` }}
            />
          ))}
        </div>
        <svg className="w-4 h-2.5 ml-1 text-white/40" viewBox="0 0 16 10" fill="none">
          <rect
            x="0.5"
            y="0.5"
            width="13"
            height="9"
            rx="1.5"
            stroke="currentColor"
            strokeWidth="1"
          />
          <rect x="14" y="3" width="2" height="4" rx="0.5" fill="currentColor" opacity="0.5" />
          <rect x="2" y="2" width="8" height="6" rx="0.5" fill="currentColor" />
        </svg>
      </div>
    </div>
  );
}

const ShortCard = memo(function ShortCard({ shortId, index }: { shortId: string; index: number }) {
  const [downloading, setDownloading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const { data } = useShortPoller(shortId, true);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleDownload = async () => {
    if (!data) return;
    setDownloading(true);
    try {
      const result = await api.downloadShort(shortId);
      window.open(result.download_url, "_blank");
    } catch {
      if (data.download_url) window.open(data.download_url, "_blank");
    } finally {
      setDownloading(false);
    }
  };

  // Loading skeleton
  if (!data) {
    return (
      <div className="glass rounded-2xl overflow-hidden">
        <div className="p-4">
          <div
            className="rounded-[20px] overflow-hidden shimmer mx-auto"
            style={{ width: 160, height: Math.round(160 * (16 / 9)) }}
          />
          <div className="mt-4 space-y-2">
            <div className="h-4 w-3/4 rounded-lg shimmer" />
            <div className="h-3 w-1/2 rounded-lg shimmer" />
            <div className="h-8 w-full rounded-xl shimmer mt-3" />
          </div>
        </div>
      </div>
    );
  }

  const isProcessing =
    data.status === SHORT_STATUS.QUEUED ||
    data.status === SHORT_STATUS.DOWNLOADING ||
    data.status === SHORT_STATUS.PROCESSING ||
    data.status === SHORT_STATUS.UPLOADING;
  const isReady = data.status === SHORT_STATUS.READY;
  const isFailed = data.status === SHORT_STATUS.FAILED;

  const stageInfo = STAGE_PROGRESS[data.status] || { pct: 0, label: data.status };

  const frameWidth = 160;
  const frameHeight = Math.round(frameWidth * (16 / 9));

  return (
    <motion.div
      className={`glass rounded-2xl overflow-hidden flex flex-col transition-all duration-500 ${
        isReady
          ? "border-emerald-500/15 shadow-[0_0_40px_rgba(52,211,153,0.06)]"
          : isFailed
            ? "border-red-500/15"
            : ""
      }`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.12, type: "spring", stiffness: 200, damping: 24 }}
    >
      <div className="p-5">
        {/* Phone frame - portrait, centered */}
        <div className="relative mx-auto" style={{ width: frameWidth, height: frameHeight }}>
          {/* Bezel */}
          <div
            className="absolute inset-0 rounded-[20px] overflow-hidden"
            style={{
              background: "var(--color-surface-1)",
              border: "2px solid rgba(139,92,246,0.2)",
              boxShadow: "0 0 0 1px rgba(0,0,0,0.4), 0 8px 32px rgba(0,0,0,0.4), 0 0 20px rgba(139,92,246,0.08)",
            }}
          >
            <PhoneStatusBar />

            {/* Processing: waveform */}
            {isProcessing && (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-violet-500/10 to-purple-500/5">
                <Waveform />
              </div>
            )}

            {/* Ready: video preview */}
            {isReady && (
              <div className="relative w-full h-full group cursor-pointer" onClick={togglePlay}>
                {data.download_url ? (
                  <video
                    ref={videoRef}
                    src={data.download_url}
                    poster={data.thumbnail_url || undefined}
                    className="w-full h-full object-cover"
                    playsInline
                    loop
                    onEnded={() => setIsPlaying(false)}
                  />
                ) : data.thumbnail_url ? (
                  <img
                    src={data.thumbnail_url}
                    alt={data.title || "Short"}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-b from-violet-500/15 to-purple-500/10 flex items-center justify-center">
                    <svg
                      className="w-10 h-10 text-violet-400/40"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                      />
                    </svg>
                  </div>
                )}
                {/* Play/pause overlay */}
                <div className={`absolute inset-0 flex items-center justify-center bg-black/20 transition-opacity ${
                  isPlaying ? "opacity-0 group-hover:opacity-100" : "opacity-100"
                }`}>
                  <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                    {isPlaying ? (
                      <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    )}
                  </div>
                </div>
                {/* Confetti burst */}
                {!isPlaying && <ConfettiBurst />}
              </div>
            )}

            {/* Failed */}
            {isFailed && (
              <div className="w-full h-full flex items-center justify-center bg-red-500/5">
                <svg
                  className="w-10 h-10 text-red-400/40"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
            )}
          </div>
        </div>

        {/* Card info */}
        <div className="mt-4">
          {/* Status badge */}
          <div className="flex items-center gap-2 mb-2">
            {isProcessing && (
              <span className="text-xs font-medium text-violet-300/80 bg-violet-500/10 px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
                <svg className="w-3 h-3 spin" viewBox="0 0 24 24" fill="none">
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeDasharray="30 70"
                  />
                </svg>
                Short #{index + 1}
              </span>
            )}
            {isReady && (
              <span className="text-xs font-medium text-emerald-400/80 bg-emerald-500/10 px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
                <svg
                  className="w-3 h-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2.5}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Ready
              </span>
            )}
            {isFailed && (
              <span className="text-xs font-medium text-red-400/80 bg-red-500/10 px-2.5 py-0.5 rounded-full">
                Failed
              </span>
            )}
            {data.is_watermarked && (
              <span className="text-[10px] text-amber-400/60 bg-amber-500/8 px-2 py-0.5 rounded-full border border-amber-500/10">
                Watermarked
              </span>
            )}
          </div>

          {/* Title */}
          {isProcessing && (
            <p className="text-sm font-medium text-white/70 mb-2">
              Generating Short #{index + 1}...
            </p>
          )}
          {isReady && (
            <h3 className="text-sm font-semibold text-white/85 mb-2 leading-snug">
              {data.title || "Untitled Short"}
            </h3>
          )}
          {isFailed && (
            <p className="text-sm text-white/50 leading-relaxed">
              {data.error_message || "An error occurred during generation"}
            </p>
          )}

          {/* Metadata */}
          {isReady && (data.duration_seconds || data.file_size_bytes) && (
            <div className="flex items-center gap-3 text-xs text-white/35 mb-3">
              {data.duration_seconds && (
                <span className="flex items-center gap-1">
                  <svg
                    className="w-3 h-3"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  {formatDuration(data.duration_seconds)}
                </span>
              )}
              {data.file_size_bytes && <span>{formatFileSize(data.file_size_bytes)}</span>}
            </div>
          )}

          {/* Progress bar (processing) */}
          {isProcessing && (
            <div className="mb-3">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] text-white/30">{stageInfo.label}</span>
                <span className="text-[10px] text-violet-400/60 tabular-nums font-medium">
                  {stageInfo.pct}%
                </span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-violet-600 to-purple-500"
                  initial={{ width: "0%" }}
                  animate={{ width: `${stageInfo.pct}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                />
              </div>
            </div>
          )}

          {/* Download button (ready) */}
          {isReady && (
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="btn-success w-full text-sm py-2.5 flex items-center justify-center gap-2"
            >
              {downloading ? (
                <>
                  <svg className="w-4 h-4 spin" viewBox="0 0 24 24" fill="none">
                    <circle
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeDasharray="30 70"
                    />
                  </svg>
                  Preparing...
                </>
              ) : (
                <>
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  Download Short
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
});

export default ShortCard;
