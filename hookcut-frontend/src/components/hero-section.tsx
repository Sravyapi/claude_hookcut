"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { Play, Heart, MessageCircle, Share2 } from "lucide-react";
import { youtubeThumbUrl } from "@/lib/utils";
import { HeroUrlInput } from "@/components/hero-url-input";

// ── Timing constants ───────────────────────────────────────────────────────────
const WAVEFORM_BARS = 32;
const HOOK_PIN_POSITIONS = [6, 22, 35, 57, 76] as const;
const DEMO_IDLE_MS = 2000;
const DEMO_LOADING_MS = 2800;
const DEMO_RESULTS_MS = 4000;
const DEMO_SHORTS_MS = 5000;
const DEMO_FADEOUT_MS = 900;

// ── Seeded waveform (no SSR hydration mismatch) ────────────────────────────────
function buildWaveform(seed: number) {
  return Array.from({ length: WAVEFORM_BARS }, (_, i) => 20 + ((i * seed + 13) % 65));
}

// ── Demo video data — 3 rotating videos ─────────────────────────────────────
const DEMO_VIDEOS = [
  {
    id: 0,
    videoId: "dQw4w9WgXcQ",
    title: "How I Built a $10M Business in 12 Months",
    channel: "MrBeast",
    initials: "MB",
    channelColor: "#FF4500",
    thumbFrom: "rgba(255,69,0,0.35)",
    thumbVia: "#0f0704",
    duration: "18:42",
    views: "52M views",
    url: "youtube.com/watch?v=dQw4w9WgXcQ",
    shortTitles: [
      "The equation inside GPT-4 nobody talks about",
      "How neural nets ACTUALLY think",
      "7 lines that beat the human brain",
    ],
    shortVideoIds: ["GkyDnMSMIuY", "TQMbvJNRpLE", "9bZkp7q19f0"],
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
  {
    id: 1,
    videoId: "erLbbextvlY",
    title: "I Survived 100 Days in Minecraft Hardcore",
    channel: "Marques Brownlee",
    initials: "MK",
    channelColor: "#E91E63",
    thumbFrom: "rgba(233,30,99,0.35)",
    thumbVia: "#0f0508",
    duration: "24:37",
    views: "18M views",
    url: "youtube.com/watch?v=erLbbextvlY",
    shortTitles: [
      "The skill that made me $1M",
      "Why 95% of side hustles fail",
      "The 3-income-stream formula",
    ],
    shortVideoIds: ["erLbbextvlY", "dWqNgzZwVJQ", "FZ0cG47msEk"],
    waveform: buildWaveform(7821),
    hooks: [
      {
        score: 9.3,
        type: "DIRECT BENEFIT",
        color: "#10B981",
        time: "0:08",
        text: "If you follow this framework, you will make your first $10,000 online within 90 days.",
        platform: "Direct-promise hooks within the first 10 seconds drive 2.8× higher completion.",
        psychology: "Specific numbers ($10K, 90 days) feel achievable and activate goal-setting behavior.",
        tip: "Always pair a specific dollar amount with a concrete timeframe.",
      },
      {
        score: 8.9,
        type: "STORY-BASED",
        color: "#FBBF24",
        time: "2:41",
        text: "Two years ago I was a junior doctor working 80-hour weeks — earning less per hour than a barista.",
        platform: "Relatable origin stories in finance content generate 5× more shares than advice-only hooks.",
        psychology: "Status contrast (doctor < barista) creates cognitive dissonance that demands resolution.",
        tip: "Lead with your lowest point — the contrast with your current position is the hook.",
      },
      {
        score: 8.2,
        type: "FEAR-BASED",
        color: "#EF4444",
        time: "7:15",
        text: "If you're relying on a single income stream in 2026, you're one layoff away from disaster.",
        platform: "Fear-based financial hooks drive 3.5× more saves — viewers bookmark for later action.",
        psychology: "Loss aversion is 2× stronger than gain motivation — fear of loss triggers immediate attention.",
        tip: "Frame the risk as imminent and personal — 'you' not 'people'.",
      },
      {
        score: 7.8,
        type: "SOCIAL PROOF",
        color: "#6366F1",
        time: "12:33",
        text: "I surveyed 500 millionaires under 30 — they all had this one thing in common.",
        platform: "Large sample sizes in social proof hooks signal research-backed credibility.",
        psychology: "Pattern recognition across successful people triggers 'what am I missing?' urgency.",
        tip: "Quantify your research sample — 500 feels more credible than 'many'.",
      },
      {
        score: 7.4,
        type: "ELIMINATION",
        color: "#94A3B8",
        time: "18:22",
        text: "It's not about working harder, it's not about luck — it's about this one mental model.",
        platform: "Elimination hooks create satisfying narrative arcs that boost watch time by 40%.",
        psychology: "Ruling out expected answers builds tension — the real answer feels like a revelation.",
        tip: "Eliminate exactly two common beliefs before revealing the third, unexpected truth.",
      },
    ],
  },
  {
    id: 2,
    videoId: "hHW1oY26kxQ",
    title: "The Most Eye Opening 10 Minutes Of Your Life",
    channel: "Veritasium",
    initials: "V",
    channelColor: "#00BCD4",
    thumbFrom: "rgba(0,188,212,0.35)",
    thumbVia: "#050d0f",
    duration: "14:23",
    views: "38M views",
    url: "youtube.com/watch?v=hHW1oY26kxQ",
    shortTitles: [
      "The 4 pillars of powerful speech",
      "Why nobody listens to you",
      "The voice trick that commands attention",
    ],
    shortVideoIds: ["hHW1oY26kxQ", "S4H_iyVMnME", "pUF5esTscZI"],
    waveform: buildWaveform(2193),
    hooks: [
      {
        score: 9.5,
        type: "PATTERN INTERRUPT",
        color: "#06B6D4",
        time: "0:04",
        text: "The human voice — it's the instrument we all play, and yet most of us have never had a single lesson.",
        platform: "Universal-truth openers on TED content get 6× more clip saves than topic introductions.",
        psychology: "Reframing something mundane (voice) as a skill gap creates instant self-awareness.",
        tip: "Start with something everyone does daily, then reveal they're doing it wrong.",
      },
      {
        score: 8.7,
        type: "AUTHORITY",
        color: "#8B5CF6",
        time: "1:52",
        text: "There are seven deadly sins of speaking — and I bet you're committing at least three right now.",
        platform: "Numbered lists with personal challenges generate the highest comment engagement on TED clips.",
        psychology: "The word 'sins' triggers moral self-evaluation — viewers must watch to absolve themselves.",
        tip: "Frame bad habits as 'sins' or 'mistakes' — moral language creates urgency.",
      },
      {
        score: 8.3,
        type: "CONTRARIAN",
        color: "#F59E0B",
        time: "4:18",
        text: "Honesty is not always the best policy — there's something more powerful called 'registered' honesty.",
        platform: "Contrarian takes on universal truths (honesty) generate 4× more debate in comments.",
        psychology: "Challenging a deeply held belief forces active processing — the brain can't ignore it.",
        tip: "Take a universally accepted truth and add a surprising qualifier.",
      },
      {
        score: 7.6,
        type: "ZERO-SECOND CLAIM",
        color: "#F97316",
        time: "6:30",
        text: "If you master just four things, you can change the world with your voice.",
        platform: "Empowerment claims with specific counts drive the highest share rates in self-improvement.",
        psychology: "'Just four things' feels manageable — low barrier to entry maximizes viewer investment.",
        tip: "Keep the number small (3-5) — it signals that mastery is within reach.",
      },
      {
        score: 7.2,
        type: "OPEN LOOP",
        color: "#60A5FA",
        time: "8:15",
        text: "There's a warm-up exercise that every great speaker does before they walk on stage — and nobody talks about it.",
        platform: "Behind-the-scenes insider knowledge hooks drive 2× more saves in public speaking content.",
        psychology: "Exclusivity ('nobody talks about') triggers fear of missing privileged information.",
        tip: "Position practical tips as industry secrets — it elevates their perceived value.",
      },
    ],
  },
] as const;

type DemoVideo = (typeof DEMO_VIDEOS)[number];
type DemoHook = DemoVideo["hooks"][number];
type Phase = "idle" | "loading" | "results" | "shorts" | "fadeout";

// Short durations matching each hook slot
const SHORT_DURATIONS = ["0:28", "0:31", "0:24"] as const;

// ── Mock YouTube thumbnail (16:9 card above search bar) ───────────────────────

function MockThumbnail({ video }: { video: DemoVideo }) {
  return (
    <div
      className="w-64 sm:w-80 rounded-xl overflow-hidden shadow-2xl border border-white/[0.07]"
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
          src={youtubeThumbUrl(video.videoId, "hqdefault")}
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
        {HOOK_PIN_POSITIONS.map((left, i) => (
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
    </div>
  );
}

// ── Waveform scanner (loading phase) ──────────────────────────────────────────

function WaveformScanner({ video }: { video: DemoVideo }) {
  return (
    <div
      className="w-full rounded-2xl border border-white/[0.06] bg-[#0D0D0D] px-5 py-4"
    >
      <div className="flex items-center justify-between mb-2.5">
        <p className="text-[10px] text-white/40 font-mono uppercase tracking-widest">
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
  const showUrl = phase === "loading" || phase === "results" || phase === "shorts" || phase === "fadeout";
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

      <span className={`flex-1 text-sm font-mono truncate transition-colors duration-300 ${showUrl ? "text-white/50" : "text-white/40"}`}>
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
      initial={{ opacity: 0, y: 10 }}
      animate={visible ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
      transition={{ delay: index * 0.08, duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
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
              <p className="text-[10px] text-white/45 leading-relaxed">{text}</p>
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

// Each short uses a distinct YouTube video thumbnail (person-focused) cropped to portrait.
function MockShortThumbnail({ index, video }: { index: number; video: DemoVideo }) {
  const shortVid = video.shortVideoIds[index] ?? video.videoId;
  return (
    <div
      className="absolute inset-0 overflow-hidden"
      style={{ background: `linear-gradient(175deg, ${video.thumbFrom} 0%, ${video.thumbVia} 60%, #050505 100%)` }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={youtubeThumbUrl(shortVid, "maxresdefault")}
        alt={`${video.channel} — short ${index + 1}`}
        className="absolute inset-0 w-full h-full object-cover"
        style={{
          objectPosition: "50% 25%",
          transform: "scale(1.25)",
          transformOrigin: "50% 25%",
          filter: "brightness(1.05) saturate(1.15) contrast(1.05)",
          transition: "opacity 0.3s",
        }}
        onError={(e) => {
          const img = e.target as HTMLImageElement;
          if (img.src.includes("maxresdefault")) {
            img.src = youtubeThumbUrl(shortVid, "hqdefault");
          } else {
            img.style.display = "none";
          }
        }}
      />
      {/* Cinematic vignette */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 75% 85% at 50% 30%, transparent 20%, rgba(0,0,0,0.6) 100%)" }}
      />
    </div>
  );
}

// ── YouTube Short card (shorts phase) ─────────────────────────────────────────

const DemoShortCard = React.memo(function DemoShortCard({
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
  const shortTitle = video.shortTitles[index] ?? captionWords;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.1, duration: 0.7, ease: "easeOut" }}
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
});

// ── Main HeroSection ───────────────────────────────────────────────────────────

export function HeroSection() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [demoIndex, setDemoIndex] = useState(0);
  const [active, setActive] = useState(false);
  const mountedRef = useRef(true);

  const video = DEMO_VIDEOS[demoIndex];

  const handleActivate = useCallback(() => setActive(true), []);

  // Autoplay loop — cycles through videos and all phases.
  useEffect(() => {
    mountedRef.current = true;
    let idx = 0;

    function wait(ms: number): Promise<void> {
      return new Promise((r) => setTimeout(r, ms));
    }

    (async () => {
      while (mountedRef.current) {
        setDemoIndex(idx);
        setPhase("idle");
        await wait(DEMO_IDLE_MS);
        if (!mountedRef.current) return;

        setPhase("loading");
        await wait(DEMO_LOADING_MS);
        if (!mountedRef.current) return;

        setPhase("results");
        await wait(DEMO_RESULTS_MS);
        if (!mountedRef.current) return;

        setPhase("shorts");
        await wait(DEMO_SHORTS_MS);
        if (!mountedRef.current) return;

        // Fade out everything before switching to next video
        setPhase("fadeout");
        await wait(DEMO_FADEOUT_MS);
        if (!mountedRef.current) return;

        idx = (idx + 1) % DEMO_VIDEOS.length;
      }
    })();

    return () => {
      mountedRef.current = false;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const showThumbnail = !active && phase === "idle";
  const showScanner   = !active && phase === "loading";
  const showHooks     = !active && (phase === "results" || phase === "shorts");
  const showShorts    = !active && phase === "shorts";
  const isFading      = phase === "fadeout";

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
            Turn long-form into viral Shorts
          </div>
          <h1 className="text-hero text-[clamp(44px,7.5vw,100px)] font-extrabold text-white leading-[1.0] tracking-[-0.04em] mb-5 font-[family-name:--font-display]">
            Find the hook.
            <br />
            <span className="text-[#E84A2F]">Stop the scroll.</span>
          </h1>
          <p className="text-white/40 text-lg leading-relaxed max-w-xl mx-auto">
            Paste a YouTube URL. Get back the 5 moments most likely to stop the scroll — scored, explained, and clipped into ready-to-post Shorts.
          </p>
        </motion.div>

        {/* ── Demo workspace ── */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
        >
          {/* ── Fade wrapper for cross-video transitions ── */}
          <div
            style={{
              opacity: isFading ? 0 : 1,
              transition: "opacity 0.8s cubic-bezier(0.22, 1, 0.36, 1)",
            }}
          >

          {/* ── Above search bar: stacked layers, pure opacity crossfade, NO layout shift ── */}
          <div className="relative mb-5" style={{ minHeight: "13rem" }}>
            {/* Thumbnail layer */}
            <div
              className="absolute inset-0 flex justify-center items-end"
              style={{ opacity: showThumbnail ? 1 : 0, transition: "opacity 0.9s cubic-bezier(0.22, 1, 0.36, 1)", pointerEvents: showThumbnail ? "auto" : "none" }}
            >
              <MockThumbnail video={video} />
            </div>
            {/* Scanner layer */}
            <div
              className="absolute inset-x-0 bottom-0"
              style={{ opacity: showScanner ? 1 : 0, transition: "opacity 0.9s cubic-bezier(0.22, 1, 0.36, 1)", pointerEvents: showScanner ? "auto" : "none" }}
            >
              <WaveformScanner video={video} />
            </div>
          </div>

          {/* Search bar */}
          {active ? (
            <HeroUrlInput />
          ) : (
            <DemoInputBar video={video} phase={phase} onActivate={handleActivate} />
          )}

          {/* ── Below search bar: CSS Grid 0fr→1fr for smooth height + opacity ── */}

          {/* HOOKS */}
          <div
            className="grid mt-4 text-left"
            style={{
              gridTemplateRows: showHooks ? "1fr" : "0fr",
              opacity: showHooks ? 1 : 0,
              transition: "grid-template-rows 0.9s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.9s cubic-bezier(0.22, 1, 0.36, 1)",
            }}
          >
            <div className="overflow-hidden">
              <div className="flex items-center justify-between px-0.5 mb-3">
                <p className="text-[10px] text-white/40 font-mono uppercase tracking-widest">
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
            </div>
          </div>

          {/* SHORTS */}
          <div
            className="grid mt-6"
            style={{
              gridTemplateRows: showShorts ? "1fr" : "0fr",
              opacity: showShorts ? 1 : 0,
              transition: "grid-template-rows 0.9s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.9s cubic-bezier(0.22, 1, 0.36, 1)",
            }}
          >
            <div className="overflow-hidden">
              {/* Section divider */}
              <div className="flex items-center gap-3 mb-4">
                <div className="flex-1 h-px bg-white/[0.05]" />
                <div className="flex items-center gap-2">
                  <span
                    className="w-1.5 h-1.5 rounded-full block animate-pulse"
                    style={{ background: video.channelColor }}
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
              <p className="text-center text-white/15 text-[9px] font-mono uppercase tracking-widest mt-4">
                MP4 · H.264 · AAC · 1080×1920 · Captions burned in
              </p>
              <div className="mt-5 text-center">
                <button
                  onClick={handleActivate}
                  className="btn-primary px-8 py-3 rounded-full text-sm font-semibold"
                >
                  Try with your video →
                </button>
                <p className="text-white/40 text-xs mt-2.5">120 minutes free · No credit card</p>
              </div>
            </div>
          </div>
          {/* close fade wrapper */}
          </div>
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
