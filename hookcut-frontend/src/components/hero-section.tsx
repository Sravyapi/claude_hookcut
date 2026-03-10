"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { HeroUrlInput } from "@/components/hero-url-input";
import {
  DEMO_VIDEOS,
  MockThumbnail,
  DemoInputBar,
  DemoShortCard,
  type Phase,
} from "@/components/hero/demo-carousel";
import { WaveformScanner } from "@/components/hero/waveform-visual";
import { DemoHookCard } from "@/components/hero/hook-timeline";

// ── Timing constants ───────────────────────────────────────────────────────────
const DEMO_IDLE_MS = 2000;
const DEMO_LOADING_MS = 2800;
const DEMO_RESULTS_MS = 4000;
const DEMO_SHORTS_MS = 5000;
const DEMO_FADEOUT_MS = 900;

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

        {/* Headline */}
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

        {/* Demo workspace */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
        >
          {/* Fade wrapper for cross-video transitions */}
          <div
            style={{
              opacity: isFading ? 0 : 1,
              transition: "opacity 0.8s cubic-bezier(0.22, 1, 0.36, 1)",
            }}
          >

          {/* Above search bar: stacked layers, pure opacity crossfade, NO layout shift */}
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

          {/* Below search bar: CSS Grid 0fr->1fr for smooth height + opacity */}

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
