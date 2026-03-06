"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Heart, MessageCircle, Share2 } from "lucide-react";
import { HeroUrlInput } from "@/components/hero-url-input";

// ── Seeded waveform (no SSR hydration mismatch) ────────────────────────────────
function buildWaveform(seed: number) {
  return Array.from({ length: 32 }, (_, i) => 20 + ((i * seed + 13) % 65));
}

// ── Demo video data (single video — Andrej Karpathy) ──────────────────────────
const DEMO_VIDEOS = [
  {
    id: 0,
    videoId: "kCc8FmEb1nY",
    title: "Let's Build GPT: From Scratch, In Code, Spelled Out",
    channel: "Andrej Karpathy",
    initials: "AK",
    channelColor: "#6366F1",
    thumbFrom: "rgba(99,102,241,0.35)",
    thumbVia: "#07070f",
    duration: "1:56:20",
    views: "4.1M views",
    url: "youtube.com/watch?v=kCc8FmEb1nY",
    shortTitles: [
      "The equation inside GPT-4 nobody talks about",
      "How neural nets ACTUALLY think",
      "7 lines that beat the human brain",
    ],
    waveform: buildWaveform(4357),
    hooks: [
      {
        score: 9.1,
        type: "CURIOSITY GAP",
        color: "#E84A2F",
        time: "3:28",
        text: "There's a single equation inside GPT-4 that most AI researchers still don't fully understand.",
        platform: "Knowledge-gap framing drives 4× rewatch rate in tech/education content.",
        psychology: "Experts feel compelled to verify 'things they should know' — triggers ego engagement.",
        tip: "Imply the viewer is missing critical knowledge, then prove they are.",
      },
      {
        score: 8.6,
        type: "CONTRARIAN",
        color: "#F59E0B",
        time: "11:17",
        text: "Everything you've read about how neural networks 'think' is wrong. Here's what's actually happening.",
        platform: "Tech contrarian hooks generate 3.2× more comments — algorithm loves comment velocity.",
        psychology: "Challenging established mental models creates productive dissonance that demands resolution.",
        tip: "The word 'actually' signals authority and inevitably triggers curiosity.",
      },
      {
        score: 8.0,
        type: "REVELATION",
        color: "#A78BFA",
        time: "22:49",
        text: "I spent 6 months building GPT-2 from scratch so you don't have to — and found something unexpected.",
        platform: "Personal investment + discovery arc drives highest completion rates in educational niches.",
        psychology: "Vicarious learning feels lower-cost — viewers get the insight without the 6 months of work.",
        tip: "Quantify your sacrifice (months, hours, failures) before sharing the payoff.",
      },
      {
        score: 7.5,
        type: "OPEN LOOP",
        color: "#60A5FA",
        time: "38:02",
        text: "The reason AI hallucinates is hiding in something called 'softmax collapse' — and nobody's talking about it.",
        platform: "Precise technical labels signal insider knowledge and filter a high-value audience.",
        psychology: "Naming an unknown phenomenon makes viewers feel they're learning something exclusive.",
        tip: "Use precise terminology — it builds credibility and creates curiosity simultaneously.",
      },
      {
        score: 7.1,
        type: "SHOCK STATISTIC",
        color: "#34D399",
        time: "51:14",
        text: "This 7-line transformer block processes more information per second than your entire brain.",
        platform: "Scale comparisons (human vs machine) are the highest-performing hook format in AI content.",
        psychology: "Concrete, visceral comparisons make abstract concepts emotionally relatable.",
        tip: "Always anchor the abstract with a human-scale comparison.",
      },
    ],
  },
] as const;

type DemoVideo = (typeof DEMO_VIDEOS)[number];
type DemoHook = DemoVideo["hooks"][number];
type Phase = "idle" | "flying" | "loading" | "results" | "shorts";

// Short durations matching each hook slot
const SHORT_DURATIONS = ["0:28", "0:31", "0:24"] as const;

// ── Mock YouTube thumbnail (16:9 card above search bar) ───────────────────────

function MockThumbnail({ video, phase }: { video: DemoVideo; phase: Phase }) {
  return (
    <motion.div
      key={`thumb-${video.id}`}
      className="w-64 sm:w-80 rounded-xl overflow-hidden shadow-2xl border border-white/[0.07]"
      style={{ transformOrigin: "50% 100%" }}
      initial={{ opacity: 0, y: -10, scale: 0.96 }}
      animate={
        phase === "flying"
          ? { opacity: 0, scale: 0.04, y: 210 }
          : { opacity: 1, y: 0, scale: 1 }
      }
      transition={
        phase === "flying"
          ? { duration: 0.5, ease: [0.4, 0, 0.8, 1] }
          : { duration: 0.45, ease: [0, 0, 0.2, 1] }
      }
    >
      {/* Thumbnail */}
      <div
        className="relative"
        style={{
          aspectRatio: "16/9",
          background: `linear-gradient(155deg, ${video.thumbFrom} 0%, ${video.thumbVia} 55%, #080808 100%)`,
        }}
      >
        {/* Real YouTube thumbnail — hides itself on error, gradient shows through */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`https://img.youtube.com/vi/${video.videoId}/hqdefault.jpg`}
          alt={video.title}
          className="absolute inset-0 w-full h-full object-cover"
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
        />

        {/* Waveform bars (visible when image fails to load) */}
        <div className="absolute inset-0 flex items-end gap-px px-3 pb-3 opacity-[0.11]">
          {video.waveform.map((h, i) => (
            <div key={i} className="flex-1 rounded-t-[1px] bg-white" style={{ height: `${h}%` }} />
          ))}
        </div>

        {/* Hook moment pins */}
        {([6, 22, 35, 57, 76] as const).map((left, i) => (
          <div
            key={i}
            className="absolute bottom-3 w-[2px] rounded-full"
            style={{
              left: `${left}%`,
              height: `${45 + (i % 3) * 18}%`,
              background: video.channelColor,
              opacity: 0.75,
              boxShadow: `0 0 5px ${video.channelColor}60`,
            }}
          />
        ))}

        {/* Dark overlay for text readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/10 to-transparent" />

        {/* Play */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            className="w-11 h-11 rounded-full flex items-center justify-center"
            style={{
              background: `${video.channelColor}25`,
              border: `1.5px solid ${video.channelColor}55`,
              backdropFilter: "blur(4px)",
            }}
          >
            <Play className="w-4 h-4 text-white fill-white ml-0.5" aria-hidden="true" />
          </div>
        </div>

        {/* Duration */}
        <div className="absolute bottom-2 right-2 bg-black/80 text-white text-[9px] font-mono px-1.5 py-0.5 rounded">
          {video.duration}
        </div>
        {/* YT badge */}
        <div className="absolute top-2 right-2 bg-[#FF0000] text-white text-[7px] font-bold px-1.5 py-0.5 rounded">
          YouTube
        </div>
        {/* Title */}
        <div className="absolute bottom-0 left-0 right-0 px-2.5 pb-7">
          <p className="text-white text-[10px] font-semibold leading-tight line-clamp-2">
            {video.title}
          </p>
        </div>
      </div>

      {/* Channel row */}
      <div className="bg-[#181818] px-3 py-2 flex items-center gap-2">
        <div
          className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[7px] font-bold shrink-0"
          style={{ background: video.channelColor }}
        >
          {video.initials}
        </div>
        <div className="min-w-0">
          <p className="text-white/60 text-[9px] font-medium truncate">{video.channel}</p>
          <p className="text-white/25 text-[8px] font-mono">{video.views}</p>
        </div>
      </div>
    </motion.div>
  );
}

// ── Waveform scanner (loading phase) ──────────────────────────────────────────

function WaveformScanner({ video }: { video: DemoVideo }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.28 }}
      className="w-full rounded-2xl border border-white/[0.06] bg-[#0D0D0D] px-5 py-4"
    >
      <div className="flex items-center justify-between mb-2.5">
        <p className="text-[10px] text-white/22 font-mono uppercase tracking-widest">
          Scanning transcript…
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
            className="text-[9px] font-mono text-white/18 flex items-center gap-1"
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
    </motion.div>
  );
}

// ── Demo input bar ─────────────────────────────────────────────────────────────

function DemoInputBar({
  video,
  phase,
  onActivate,
}: {
  video: DemoVideo;
  phase: Phase;
  onActivate: () => void;
}) {
  const showUrl = phase === "loading" || phase === "results" || phase === "shorts";
  const isLoading = phase === "loading";

  return (
    <button
      onClick={onActivate}
      className={`flex items-center gap-3 w-full rounded-2xl border px-5 py-4 text-left transition-all duration-500 cursor-text ${
        isLoading
          ? "border-[#E84A2F]/40 bg-[#E84A2F]/[0.04]"
          : showUrl
          ? "border-white/[0.12] bg-white/[0.03]"
          : "border-white/[0.08] bg-white/[0.02] hover:border-white/[0.13]"
      }`}
      aria-label="Click to analyze your own YouTube video"
    >
      <svg className="w-4 h-4 shrink-0 text-[#FF0000]" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
      </svg>

      <span className={`flex-1 text-sm font-mono truncate transition-colors duration-300 ${showUrl ? "text-white/50" : "text-white/18"}`}>
        {showUrl ? video.url : "Paste a YouTube URL to analyze…"}
      </span>

      {isLoading ? (
        <span className="flex items-center gap-2 shrink-0">
          <motion.span
            className="w-3.5 h-3.5 rounded-full border-2 border-[#E84A2F] border-t-transparent block"
            animate={{ rotate: 360 }}
            transition={{ duration: 0.75, repeat: Infinity, ease: "linear" }}
            aria-hidden="true"
          />
          <motion.span
            className="text-[#E84A2F] text-xs font-medium"
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 1.3, repeat: Infinity }}
          >
            Analyzing…
          </motion.span>
        </span>
      ) : (
        <span className="text-xs px-3.5 py-1.5 rounded-full bg-[#E84A2F] text-white font-semibold shrink-0">
          {showUrl ? "↵" : "Analyze →"}
        </span>
      )}
    </button>
  );
}

// ── Hook card (results phase) ──────────────────────────────────────────────────

function DemoHookCard({
  hook,
  index,
  visible,
  isTop,
}: {
  hook: DemoHook;
  index: number;
  visible: boolean;
  isTop: boolean;
}) {
  const circ = 2 * Math.PI * 14;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={visible ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ delay: index * 0.1, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className={`rounded-xl border bg-[#0f0f0f] p-3.5 flex flex-col gap-2.5 ${
        isTop ? "border-white/[0.09]" : "border-white/[0.04]"
      }`}
    >
      <div className="flex items-center gap-2.5">
        {/* Score ring */}
        <div className="relative shrink-0 w-9 h-9">
          <svg viewBox="0 0 32 32" className="w-full h-full -rotate-90" aria-hidden="true">
            <circle cx="16" cy="16" r="14" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="2.5" />
            <motion.circle
              cx="16" cy="16" r="14"
              fill="none" stroke={hook.color} strokeWidth="2.5" strokeLinecap="round"
              strokeDasharray={circ}
              initial={{ strokeDashoffset: circ }}
              animate={visible ? { strokeDashoffset: circ * (1 - hook.score / 10) } : { strokeDashoffset: circ }}
              transition={{ duration: 0.9, ease: "easeOut", delay: index * 0.07 + 0.15 }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[9px] font-bold font-mono" style={{ color: hook.color }}>{hook.score}</span>
          </div>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span
              className="text-[7.5px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded"
              style={{ background: `${hook.color}18`, color: hook.color }}
            >
              {hook.type}
            </span>
            <span className="text-white/20 text-[9px] font-mono">{hook.time}</span>
          </div>
        </div>
      </div>

      <p className="text-white/65 text-[11.5px] leading-relaxed">{hook.text}</p>

      {isTop ? (
        <div className="border-t border-white/[0.05] pt-2.5 flex flex-col gap-1.5">
          {(
            [
              ["Platform", hook.platform, "text-white/20"],
              ["Psychology", hook.psychology, "text-white/20"],
              ["Tip", hook.tip, hook.color + "99"],
            ] as const
          ).map(([label, text, labelColor]) => (
            <div key={label} className="flex gap-1.5">
              <span className="text-[8px] font-bold uppercase tracking-wider pt-px shrink-0 w-16" style={{ color: labelColor }}>
                {label}
              </span>
              <p className="text-[10px] text-white/32 leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[9.5px] font-mono leading-relaxed border-t border-white/[0.04] pt-2 line-clamp-1" style={{ color: `${hook.color}60` }}>
          {hook.tip}
        </p>
      )}
    </motion.div>
  );
}

// ── Mock Short thumbnail ───────────────────────────────────────────────────────

// Uses maxresdefault.jpg (1280×720) — high-res, not the terrible 120×90 frame grabs.
// Each card zooms into a different region + applies a distinct color grade so they
// look like 3 intentionally edited Short thumbnails, not 3 copies of the same frame.
const SHORT_CROP_CONFIGS = [
  // Card 0 — punch in left, warm grade (speaker face region)
  { pos: "28% 18%",  scale: 1.35, filter: "brightness(1.08) saturate(1.18) contrast(1.05)" },
  // Card 1 — center-upper, punchy contrast (whiteboard/code region)
  { pos: "50% 22%",  scale: 1.2,  filter: "brightness(0.96) saturate(1.22) contrast(1.1)" },
  // Card 2 — right side, slight cool lift (side-angle region)
  { pos: "72% 20%",  scale: 1.3,  filter: "brightness(1.04) saturate(1.1) hue-rotate(8deg)" },
] as const;

function MockShortThumbnail({ index, video }: { index: number; video: DemoVideo }) {
  const cfg = SHORT_CROP_CONFIGS[index];
  return (
    <div
      className="absolute inset-0 overflow-hidden"
      style={{ background: `linear-gradient(175deg, ${video.thumbFrom} 0%, ${video.thumbVia} 60%, #050505 100%)` }}
    >
      {/* High-res thumbnail, zoomed + cropped to portrait region */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`https://img.youtube.com/vi/${video.videoId}/maxresdefault.jpg`}
        alt={`${video.channel} — hook moment ${index + 1}`}
        className="absolute inset-0 w-full h-full object-cover"
        style={{
          objectPosition: cfg.pos,
          transform: `scale(${cfg.scale})`,
          transformOrigin: cfg.pos,
          filter: cfg.filter,
          transition: "opacity 0.3s",
        }}
        onError={(e) => {
          // Fall back to hqdefault (480×360) if maxres isn't available
          const img = e.target as HTMLImageElement;
          if (img.src.includes("maxresdefault")) {
            img.src = `https://img.youtube.com/vi/${video.videoId}/hqdefault.jpg`;
          } else {
            img.style.display = "none";
          }
        }}
      />
      {/* Cinematic vignette — darkens edges, keeps subject bright */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 75% 85% at 50% 35%, transparent 20%, rgba(0,0,0,0.55) 100%)" }}
      />
      {/* Channel-color grade at top */}
      <div
        className="absolute inset-x-0 top-0 h-2/5 pointer-events-none"
        style={{ background: `linear-gradient(to bottom, ${video.channelColor}40, transparent)` }}
      />
    </div>
  );
}

// ── YouTube Short card (shorts phase) ─────────────────────────────────────────

function DemoShortCard({
  hook,
  video,
  index,
}: {
  hook: DemoHook;
  video: DemoVideo;
  index: number;
}) {
  const duration = SHORT_DURATIONS[index];
  const captionWords = hook.text.split(" ").slice(0, 6).join(" ");
  const shortTitle = (video.shortTitles as unknown as string[])[index] ?? captionWords;

  return (
    <motion.div
      initial={{ opacity: 0, y: 32, scale: 0.93 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.18, type: "spring", stiffness: 180, damping: 20 }}
      className="flex-1 flex flex-col gap-2 cursor-pointer"
    >
      {/* ── Portrait card (no text overlay) ── */}
      <div
        className="relative rounded-2xl overflow-hidden border border-white/[0.08]"
        style={{ aspectRatio: "9 / 16" }}
      >
        <MockShortThumbnail index={index} video={video} />

        {/* Bottom scrim for caption readability */}
        <div className="absolute inset-0" style={{ background: "linear-gradient(to bottom, transparent 55%, rgba(0,0,0,0.88) 100%)" }} />

        {/* Reel indicator dots */}
        <div className="absolute top-2.5 left-0 right-0 flex justify-center gap-1" aria-hidden="true">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="rounded-full"
              style={{
                width: i === index ? "14px" : "4px",
                height: "3px",
                background: i === index ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.25)",
              }}
            />
          ))}
        </div>

        {/* Channel avatar (top-left) */}
        <div className="absolute top-7 left-2.5 flex items-center gap-1.5">
          <div
            className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[7px] font-bold border border-white/25 shrink-0"
            style={{ background: video.channelColor }}
          >
            {video.initials}
          </div>
          <span className="text-white/80 text-[8px] font-semibold leading-none" style={{ textShadow: "0 1px 4px rgba(0,0,0,0.8)" }}>
            {video.channel.split(" ")[0]}
          </span>
        </div>

        {/* Right action icons */}
        <div className="absolute right-2 top-1/2 -translate-y-4 flex flex-col items-center gap-3.5" aria-hidden="true">
          <div className="flex flex-col items-center gap-0.5">
            <Heart className="w-4 h-4 text-white/60" />
            <span className="text-[6px] text-white/30 font-mono">—</span>
          </div>
          <div className="flex flex-col items-center gap-0.5">
            <MessageCircle className="w-4 h-4 text-white/60" />
            <span className="text-[6px] text-white/30 font-mono">—</span>
          </div>
          <Share2 className="w-3.5 h-3.5 text-white/60" />
        </div>

        {/* Burned-in caption at bottom */}
        <div className="absolute bottom-3 left-2.5 right-8">
          <span
            className="text-white font-bold leading-loose"
            style={{
              fontSize: "clamp(7px, 3%, 8.5px)",
              background: video.channelColor,
              padding: "2px 5px",
              borderRadius: "2px",
              boxDecorationBreak: "clone",
              WebkitBoxDecorationBreak: "clone",
            }}
          >
            {captionWords}
          </span>
        </div>
      </div>

      {/* ── Title + duration below the card ── */}
      <div className="px-0.5">
        <p className="text-white/85 text-[11px] font-semibold leading-snug mb-0.5">{shortTitle}</p>
        <span className="text-white/25 text-[9px] font-mono">{duration}</span>
      </div>
    </motion.div>
  );
}

// ── Main HeroSection ───────────────────────────────────────────────────────────

export function HeroSection() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [active, setActive] = useState(false);
  const mountedRef = useRef(true);

  const video = DEMO_VIDEOS[0];

  const handleActivate = useCallback(() => setActive(true), []);

  // Run once on mount — demo plays through and stays on "shorts" forever.
  // Empty deps intentional: active/phase are not deps because we never want
  // this sequence to restart. StrictMode double-invoke is harmless (cleanup
  // clears timers and the second mount replays correctly).
  useEffect(() => {
    mountedRef.current = true;

    const safe = (fn: () => void) => () => {
      if (mountedRef.current) fn();
    };

    const timers = [
      setTimeout(safe(() => setPhase("flying")),   1600),
      setTimeout(safe(() => setPhase("loading")),  2450),
      setTimeout(safe(() => setPhase("results")),  5600),
      setTimeout(safe(() => setPhase("shorts")),  12200),
    ];

    return () => {
      mountedRef.current = false;
      timers.forEach(clearTimeout);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const showThumbnail = !active && (phase === "idle" || phase === "flying");
  const showScanner   = !active && phase === "loading";
  const showHooks     = !active && (phase === "results" || phase === "shorts");
  const showShorts    = !active && phase === "shorts";

  return (
    <section
      className="relative bg-[#0A0A0A] overflow-hidden flex flex-col items-center justify-center px-6 pt-24 pb-20"
      style={{ minHeight: "100svh" }}
      aria-label="Hero"
    >
      {/* Background grid + glow */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px)`,
            backgroundSize: "64px 64px",
          }}
        />
        <div
          className="absolute inset-0"
          style={{ background: "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(232,74,47,0.06), transparent)" }}
        />
      </div>

      <div className="relative w-full max-w-3xl mx-auto text-center">

        {/* ── Headline ── */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="mb-10"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#E84A2F]/[0.1] border border-[#E84A2F]/20 text-[#E84A2F] text-xs font-semibold mb-7">
            <span className="w-1.5 h-1.5 rounded-full bg-[#E84A2F] animate-pulse" aria-hidden="true" />
            AI Hook Detection for YouTube Shorts
          </div>
          <h1 className="text-[clamp(44px,7.5vw,100px)] font-extrabold text-white leading-[1.0] tracking-[-0.04em] mb-5 font-[family-name:--font-display]">
            Find the hook.
            <br />
            <span className="text-[#E84A2F]">Stop the scroll.</span>
          </h1>
          <p className="text-white/40 text-lg leading-relaxed max-w-xl mx-auto">
            Paste any YouTube URL. HookCut finds the 5 moments most likely to go viral —
            scored, explained, and ready to post as Shorts.
          </p>
        </motion.div>

        {/* ── Demo workspace ── */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
        >
          {/* Thumbnail zone (idle/flying) and waveform scanner (loading) */}
          <AnimatePresence>
            {showThumbnail && (
              <motion.div
                key={`thumb-${video.id}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4, delay: 0.3 }}
                className="flex justify-center items-end mb-5"
                style={{ minHeight: "13rem" }}
              >
                <MockThumbnail video={video} phase={phase} />
              </motion.div>
            )}
            {showScanner && (
              <motion.div
                key="scanner"
                className="mb-5"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.35 }}
              >
                <WaveformScanner video={video} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Search bar */}
          {active ? (
            <HeroUrlInput />
          ) : (
            <DemoInputBar video={video} phase={phase} onActivate={handleActivate} />
          )}

          {/* ── Results area: hooks persist, shorts appear below ── */}

          {/* HOOKS — stays visible through shorts phase */}
          <AnimatePresence>
            {showHooks && (
              <motion.div
                key="hooks"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, transition: { duration: 0.5 } }}
                transition={{ duration: 0.4, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
                className="mt-4 text-left"
              >
                <div className="flex items-center justify-between px-0.5 mb-3">
                  <p className="text-[10px] text-white/18 font-mono uppercase tracking-widest">
                    5 hook moments · {video.channel}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ background: video.channelColor }} />
                    <span className="text-[9px] font-mono" style={{ color: `${video.channelColor}90` }}>
                      top results
                    </span>
                  </div>
                </div>

                {/* Top 2 — full detail */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
                  {video.hooks.slice(0, 2).map((hook, i) => (
                    <DemoHookCard key={hook.type} hook={hook} index={i} visible={showHooks} isTop={true} />
                  ))}
                </div>
                {/* Bottom 3 — compact */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {video.hooks.slice(2).map((hook, i) => (
                    <DemoHookCard key={hook.type} hook={hook} index={i + 2} visible={showHooks} isTop={false} />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* SHORTS — slide in below hooks */}
          <AnimatePresence>
            {showShorts && (
              <motion.div
                key="shorts"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, transition: { duration: 0.5 } }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                className="mt-6"
              >
                {/* Section divider */}
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex-1 h-px bg-white/[0.05]" />
                  <div className="flex items-center gap-2">
                    <motion.span
                      className="w-1.5 h-1.5 rounded-full block"
                      style={{ background: video.channelColor }}
                      animate={{ opacity: [1, 0.3, 1] }}
                      transition={{ duration: 0.85, repeat: Infinity }}
                    />
                    <span className="text-[10px] text-white/25 font-mono uppercase tracking-widest whitespace-nowrap">
                      3 Shorts · ready to post
                    </span>
                  </div>
                  <div className="flex-1 h-px bg-white/[0.05]" />
                </div>

                {/* Short cards — flex row */}
                <div className="flex gap-3 justify-center">
                  {video.hooks.slice(0, 3).map((hook, i) => (
                    <DemoShortCard key={hook.type} hook={hook} video={video} index={i} />
                  ))}
                </div>

                {/* Specs + CTA */}
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.9, duration: 0.5 }}
                  className="text-center text-white/15 text-[9px] font-mono uppercase tracking-widest mt-4"
                >
                  MP4 · H.264 · AAC · 1080×1920 · Captions burned in
                </motion.p>
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.1, duration: 0.4 }}
                  className="mt-5 text-center"
                >
                  <button
                    onClick={handleActivate}
                    className="btn-primary px-8 py-3 rounded-full text-sm font-semibold"
                  >
                    Try with your video →
                  </button>
                  <p className="text-white/18 text-xs mt-2.5">120 minutes free · No credit card</p>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Scroll cue */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2.5, duration: 0.8 }}
        className="absolute bottom-7 left-1/2 -translate-x-1/2"
        aria-hidden="true"
      >
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ repeat: Infinity, duration: 2.2, ease: "easeInOut" }}
          className="w-5 h-8 rounded-full border border-white/[0.09] flex items-start justify-center pt-1.5"
        >
          <div className="w-1 h-2 rounded-full bg-white/18" />
        </motion.div>
      </motion.div>
    </section>
  );
}
