"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Play } from "lucide-react";

const DEMO_SHORTS = [
  {
    hookText: "Nobody tells you this about passive income as a creator...",
    score: 9.2,
    duration: "0:47",
    scoreColor: "#E84A2F",
    bgFrom: "rgba(232,74,47,0.35)",
    bgVia: "#140806",
    captionColor: "#E84A2F",
  },
  {
    hookText: "I lost $47,000 in a single week doing THIS.",
    score: 8.7,
    duration: "0:38",
    scoreColor: "#F59E0B",
    bgFrom: "rgba(217,119,6,0.3)",
    bgVia: "#130f04",
    captionColor: "#F59E0B",
  },
  {
    hookText: "Every YouTube guru telling you to 'just upload more' is lying.",
    score: 8.1,
    duration: "0:52",
    scoreColor: "#A78BFA",
    bgFrom: "rgba(139,92,246,0.3)",
    bgVia: "#0e0812",
    captionColor: "#A78BFA",
  },
] as const;

function ShortCard({
  short,
  index,
}: {
  short: (typeof DEMO_SHORTS)[number];
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 48, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.65,
        delay: index * 0.15,
        ease: [0.22, 1, 0.36, 1],
      }}
      className="relative rounded-2xl overflow-hidden border border-white/[0.07] shadow-2xl group cursor-pointer"
      style={{ aspectRatio: "9 / 16" }}
    >
      {/* Gradient background */}
      <div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(to bottom, ${short.bgFrom}, ${short.bgVia} 55%, #080808)`,
        }}
      />

      {/* Subtle noise texture */}
      <div
        className="absolute inset-0 opacity-[0.04] mix-blend-overlay"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        }}
      />

      {/* Score badge — top right */}
      <div className="absolute top-3 right-3 flex items-center gap-1 bg-black/55 backdrop-blur-sm rounded-full px-2.5 py-1 border border-white/10">
        <div
          className="w-1.5 h-1.5 rounded-full"
          style={{ background: short.scoreColor }}
          aria-hidden="true"
        />
        <span className="text-white text-[10px] font-bold font-mono">{short.score}</span>
      </div>

      {/* "Short" label — top left */}
      <div className="absolute top-3 left-3 bg-black/55 backdrop-blur-sm rounded px-2 py-0.5 border border-white/[0.08]">
        <span className="text-white/50 text-[8px] font-semibold uppercase tracking-widest">
          Short
        </span>
      </div>

      {/* Play button — center */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-14 h-14 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center transition-transform duration-200 group-hover:scale-110">
          <Play className="w-6 h-6 text-white fill-white ml-0.5" aria-hidden="true" />
        </div>
      </div>

      {/* Caption + metadata — bottom */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent pt-12 px-3 pb-3">
        {/* Burned-in caption simulation */}
        <div className="mb-3 leading-relaxed">
          <span
            className="text-white text-[12px] font-bold"
            style={{
              background: short.captionColor,
              padding: "2px 5px",
              borderRadius: "2px",
              boxDecorationBreak: "clone",
              WebkitBoxDecorationBreak: "clone",
              lineHeight: 1.85,
            }}
          >
            {short.hookText.split(" ").slice(0, 6).join(" ")}
          </span>
        </div>

        {/* Duration + resolution */}
        <div className="flex items-center justify-between">
          <span className="text-white/35 text-[10px] font-mono">{short.duration}</span>
          <span className="text-white/25 text-[10px]">1080×1920</span>
        </div>

        {/* Download bar mock */}
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 h-0.5 rounded-full bg-white/10">
            <div
              className="h-full rounded-full"
              style={{
                width: `${65 + index * 10}%`,
                background: short.captionColor,
                opacity: 0.6,
              }}
            />
          </div>
          <span
            className="text-[9px] font-semibold"
            style={{ color: short.captionColor, opacity: 0.8 }}
          >
            Ready
          </span>
        </div>
      </div>
    </motion.div>
  );
}

export function ShortsDemo() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <section
      ref={ref}
      className="bg-[#0A0A0A] py-24 px-6 border-t border-white/[0.04]"
    >
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="mb-12 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-5"
        >
          <div>
            <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
              Generated Shorts
            </p>
            <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-white tracking-[-0.03em] leading-[1.05] font-[family-name:--font-display]">
              Hooks become Shorts.
              <br />
              In under 2 minutes.
            </h2>
          </div>
          <p className="text-white/30 text-sm max-w-xs leading-relaxed sm:text-right">
            Select up to 3 hooks, pick a caption style, and HookCut generates
            ready-to-post 9:16 clips — no editing software needed.
          </p>
        </motion.div>

        {/* Short cards grid */}
        <div className="grid grid-cols-3 gap-3 sm:gap-5 max-w-xl mx-auto">
          {DEMO_SHORTS.map((short, i) => (
            <div key={i}>
              {inView && <ShortCard short={short} index={i} />}
            </div>
          ))}
        </div>

        {/* Caption below grid */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : { opacity: 0 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="text-center text-white/20 text-xs mt-8 font-mono uppercase tracking-widest"
        >
          MP4 · H.264 · AAC · Captions burned in
        </motion.p>
      </div>
    </section>
  );
}
