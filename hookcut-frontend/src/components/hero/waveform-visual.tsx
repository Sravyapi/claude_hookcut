"use client";

import React, { memo } from "react";
import { motion } from "framer-motion";
import type { DemoVideo } from "./demo-carousel";

interface WaveformScannerProps {
  video: DemoVideo;
}

export const WaveformScanner = memo(function WaveformScanner({ video }: WaveformScannerProps) {
  return (
    <div
      className="w-full rounded-2xl border border-white/[0.06] bg-[#0D0D0D] px-5 py-4"
    >
      <div className="flex items-center justify-between mb-2.5">
        <p className="text-[10px] text-white/40 font-mono uppercase tracking-widest">
          Scanning transcript\u2026
        </p>
        <motion.span
          className="text-[10px] font-mono"
          style={{ color: video.channelColor }}
          animate={{ opacity: [1, 0.35, 1] }}
          transition={{ duration: 1.1, repeat: Infinity }}
        >
          {video.channel}
        </motion.span>
      </div>

      {/* Waveform */}
      <div className="flex items-end gap-px h-9">
        {video.waveform.map((h, i) => (
          <motion.div
            key={i}
            className="flex-1 rounded-t-[1px]"
            style={{ height: `${h}%` }}
            animate={{
              backgroundColor: [
                "rgba(232,74,47,0.10)",
                "rgba(232,74,47,0.48)",
                "rgba(232,74,47,0.10)",
              ],
            }}
            transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.028, ease: "easeInOut" }}
          />
        ))}
      </div>

      {/* V1 feature labels */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2.5">
        {(
          [
            ["Silence trimmed", 0],
            ["Audio normalized", 0.4],
            ["Complete thoughts detected", 0.8],
            ["Filler removed", 1.2],
          ] as const
        ).map(([label, delay]) => (
          <motion.span
            key={label}
            className="text-[9px] font-mono text-white/40 flex items-center gap-1"
            animate={{ opacity: [0.25, 0.65, 0.25] }}
            transition={{ duration: 2.2, repeat: Infinity, delay }}
          >
            <span
              className="w-1 h-1 rounded-full inline-block"
              style={{ background: `${video.channelColor}80` }}
            />
            {label}
          </motion.span>
        ))}
      </div>
    </div>
  );
});
