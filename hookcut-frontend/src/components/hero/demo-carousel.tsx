"use client";

import React, { memo } from "react";
import { motion } from "framer-motion";
import { Play, Heart, MessageCircle, Share2 } from "lucide-react";
import { youtubeThumbUrl } from "@/lib/utils";

// ── Timing constants ───────────────────────────────────────────────────────────
const HOOK_PIN_POSITIONS = [6, 22, 35, 57, 76] as const;
const SHORT_DURATIONS = ["0:28", "0:31", "0:24"] as const;

// ── Seeded waveform (no SSR hydration mismatch) ────────────────────────────────
function buildWaveform(seed: number) {
  return Array.from({ length: 32 }, (_, i) => 20 + ((i * seed + 13) % 65));
}

// ── Demo video data — 3 rotating videos ─────────────────────────────────────
export const DEMO_VIDEOS = [
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

export type DemoVideo = (typeof DEMO_VIDEOS)[number];
export type DemoHook = DemoVideo["hooks"][number];

// ── Mock YouTube thumbnail (16:9 card above search bar) ───────────────────────

export const MockThumbnail = memo(function MockThumbnail({ video }: { video: DemoVideo }) {
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
});

// ── Demo input bar ─────────────────────────────────────────────────────────────

export type Phase = "idle" | "loading" | "results" | "shorts" | "fadeout";

interface DemoInputBarProps {
  video: DemoVideo;
  phase: Phase;
  onActivate: () => void;
}

export const DemoInputBar = memo(function DemoInputBar({
  video,
  phase,
  onActivate,
}: DemoInputBarProps) {
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
        {showUrl ? video.url : "Paste a YouTube URL to analyze\u2026"}
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
            Analyzing\u2026
          </motion.span>
        </span>
      ) : (
        <span className="text-xs px-3.5 py-1.5 rounded-full bg-[#E84A2F] text-white font-semibold shrink-0">
          {showUrl ? "\u21B5" : "Analyze \u2192"}
        </span>
      )}
    </button>
  );
});

// ── Mock Short thumbnail ───────────────────────────────────────────────────────

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
        alt={`${video.channel} \u2014 short ${index + 1}`}
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

export const DemoShortCard = memo(function DemoShortCard({
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
      {/* Portrait card (no text overlay) */}
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
            <span className="text-[6px] text-white/30 font-mono">&mdash;</span>
          </div>
          <div className="flex flex-col items-center gap-0.5">
            <MessageCircle className="w-4 h-4 text-white/60" />
            <span className="text-[6px] text-white/30 font-mono">&mdash;</span>
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

      {/* Title + duration below the card */}
      <div className="px-0.5">
        <p className="text-white/85 text-[11px] font-semibold leading-snug mb-0.5">{shortTitle}</p>
        <span className="text-white/25 text-[9px] font-mono">{duration}</span>
      </div>
    </motion.div>
  );
});
