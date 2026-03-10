"use client";

import { useEffect, useRef, useState } from "react";
import { HeroSection } from "./hero-section";

export function HeroScrollAnimation() {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  useEffect(() => {
    if (prefersReducedMotion) return;
    if (!containerRef.current || !contentRef.current) return;

    let cleanup: (() => void) | undefined;

    async function initGSAP() {
      const gsapModule = await import("gsap");
      const { ScrollTrigger } = await import("gsap/ScrollTrigger");
      const gsap = gsapModule.default || gsapModule;
      gsap.registerPlugin(ScrollTrigger);

      const container = containerRef.current;
      const content = contentRef.current;
      if (!container || !content) return;

      // Query all animated elements
      const q = (sel: string) => content.querySelector<HTMLElement>(`[data-hero="${sel}"]`);
      const qAll = (sel: string) => content.querySelectorAll<HTMLElement>(`[data-hero="${sel}"]`);

      const headline = q("headline");
      const thumbnailZone = q("thumbnail-zone");
      const thumbnail = q("thumbnail");
      const scannerZone = q("scanner-zone");
      const waveformScanner = q("waveform-scanner");
      const searchBar = q("search-bar");
      const searchBarIdle = q("search-bar-idle");
      const searchBarAnalyzing = q("search-bar-analyzing");
      const searchBarResults = q("search-bar-results");
      const scanLine = q("scan-line");
      const hooksSection = q("hooks-section");
      const hookCards = qAll("hook-card");
      const scoreRings = qAll("score-ring");
      const shortsSection = q("shorts-section");
      const shortCards = qAll("short-card");
      const specs = q("specs");
      const cta = q("cta");
      const scrollCue = q("scroll-cue");
      const waveformBars = qAll("waveform-bar");

      if (!thumbnail || !searchBar) return;

      // ── Initial states ──
      gsap.set(headline, { autoAlpha: 1 });
      gsap.set(thumbnail, { autoAlpha: 1, scale: 1, x: 0, y: 0 });
      gsap.set(scrollCue, { autoAlpha: 0.6 });

      const circ = 2 * Math.PI * 14;

      // ── Build master timeline ──
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: container,
          start: "top top",
          end: "bottom bottom",
          scrub: 0.8,
        },
      });

      // ════════════════════════════════════════════════════════════════════
      // ACT 1: THUMBNAIL SUCKED INTO SEARCH BAR (0% → 30%)
      // ════════════════════════════════════════════════════════════════════

      // Scroll cue fades out immediately
      tl.to(scrollCue, { autoAlpha: 0, duration: 0.02 }, 0);

      // --- Thumbnail anticipation (0% → 5%) ---
      // Slight compress before the suck-in
      tl.to(thumbnail, {
        scaleY: 0.95,
        duration: 0.05,
        ease: "power1.in",
      }, 0.0);

      // --- Thumbnail suck-in (5% → 22%) ---
      // Non-linear scale + position toward search bar
      tl.to(thumbnail, {
        scale: 0.04,
        y: 210,
        scaleY: 1, // release the compress
        duration: 0.17,
        ease: "power2.in",
      }, 0.05);

      // Clip-path shrinks as it enters the bar
      tl.to(thumbnail, {
        clipPath: "inset(20% 30% 20% 30% round 50%)",
        duration: 0.12,
        ease: "power1.in",
      }, 0.08);

      // Fade out at the end of suck-in
      tl.to(thumbnail, {
        autoAlpha: 0,
        duration: 0.03,
      }, 0.20);

      // --- Amber glow on search bar (peaks at thumbnail disappearance) ---
      if (searchBarIdle) {
        tl.to(searchBarIdle, {
          boxShadow: "0 0 40px 8px rgba(245, 158, 11, 0.15)",
          borderColor: "rgba(245, 158, 11, 0.4)",
          duration: 0.06,
          ease: "power1.out",
        }, 0.16);
        tl.to(searchBarIdle, {
          boxShadow: "0 0 0 0 rgba(245, 158, 11, 0)",
          borderColor: "rgba(255, 255, 255, 0.08)",
          duration: 0.06,
          ease: "power1.in",
        }, 0.22);
      }

      // --- Scan line sweeps across search bar (15% → 28%) ---
      if (scanLine) {
        tl.set(scanLine, { autoAlpha: 1, left: "0%" }, 0.15);
        tl.to(scanLine, {
          left: "100%",
          duration: 0.13,
          ease: "none",
        }, 0.15);
        tl.set(scanLine, { autoAlpha: 0 }, 0.28);
      }

      // --- Thumbnail zone collapses (22% → 28%) ---
      if (thumbnailZone) {
        tl.to(thumbnailZone, {
          height: 0,
          minHeight: 0,
          marginBottom: 0,
          autoAlpha: 0,
          duration: 0.06,
          ease: "power2.inOut",
        }, 0.22);
      }

      // --- Headline fades & scales down (22% → 38%) to make room for cards ---
      if (headline) {
        tl.to(headline, {
          autoAlpha: 0,
          scale: 0.92,
          y: -20,
          duration: 0.16,
          ease: "power2.inOut",
        }, 0.22);
      }

      // --- Scanner zone collapses after waveform done (40% → 44%) ---
      if (scannerZone) {
        tl.to(scannerZone, {
          height: 0,
          minHeight: 0,
          marginBottom: 0,
          autoAlpha: 0,
          duration: 0.04,
          ease: "power2.inOut",
        }, 0.40);
      }

      // ════════════════════════════════════════════════════════════════════
      // ACT 1.5: ANALYZING STATE (28% → 42%)
      // ════════════════════════════════════════════════════════════════════

      // Search bar idle → analyzing transition
      if (searchBarIdle && searchBarAnalyzing) {
        tl.to(searchBarIdle, { autoAlpha: 0, duration: 0.03 }, 0.28);
        tl.to(searchBarAnalyzing, { autoAlpha: 1, duration: 0.03 }, 0.29);
      }

      // Waveform scanner appears
      if (waveformScanner && scannerZone) {
        tl.to(waveformScanner, {
          autoAlpha: 1,
          scale: 1,
          duration: 0.04,
          ease: "power2.out",
        }, 0.30);

        // Waveform bars pulse (staggered color)
        if (waveformBars.length > 0) {
          tl.to(waveformBars, {
            backgroundColor: "rgba(232,74,47,0.48)",
            duration: 0.04,
            stagger: { each: 0.001, from: "start" },
            ease: "power1.inOut",
          }, 0.32);
          tl.to(waveformBars, {
            backgroundColor: "rgba(232,74,47,0.10)",
            duration: 0.04,
            stagger: { each: 0.001, from: "start" },
            ease: "power1.inOut",
          }, 0.36);
        }

        // Waveform scanner fades out
        tl.to(waveformScanner, {
          autoAlpha: 0,
          duration: 0.03,
          ease: "power1.in",
        }, 0.40);
      }

      // Search bar analyzing → results transition
      if (searchBarAnalyzing && searchBarResults) {
        tl.to(searchBarAnalyzing, { autoAlpha: 0, duration: 0.02 }, 0.41);
        tl.to(searchBarResults, { autoAlpha: 1, duration: 0.02 }, 0.42);
      }

      // ════════════════════════════════════════════════════════════════════
      // ACT 2: HOOK CARDS DEAL OUT (42% → 62%)
      // ════════════════════════════════════════════════════════════════════

      // Hooks section container appears
      if (hooksSection) {
        tl.to(hooksSection, { autoAlpha: 1, duration: 0.02 }, 0.43);
      }

      // Cards deal out with stagger — physical "dealt" feeling
      // Secondary cards first (indices 1-4), primary card (index 0) LAST
      const dealOrder = [1, 2, 3, 4, 0];
      const cardElements = Array.from(hookCards);

      dealOrder.forEach((cardIdx, dealIdx) => {
        const card = cardElements[cardIdx];
        if (!card) return;

        const isPrimary = cardIdx === 0;
        const startRotation = (Math.random() - 0.5) * 16; // ±8deg
        const endRotation = isPrimary ? 0 : (Math.random() - 0.5) * 6; // ±3deg or 0

        // Set initial state
        gsap.set(card, {
          autoAlpha: 0,
          y: 40,
          rotation: startRotation,
          scale: 0.85,
        });

        const dealStart = 0.44 + dealIdx * 0.03; // 0.03 = ~0.12s at scrub 0.8

        if (isPrimary) {
          // Primary card: bigger overshoot — scale 0.85 → 1.06 → 1.0
          tl.to(card, {
            autoAlpha: 1,
            y: 0,
            rotation: 0,
            scale: 1.06,
            duration: 0.04,
            ease: "back.out(1.7)",
          }, dealStart);
          tl.to(card, {
            scale: 1.0,
            duration: 0.02,
            ease: "power2.out",
          }, dealStart + 0.04);
        } else {
          tl.to(card, {
            autoAlpha: 1,
            y: 0,
            rotation: endRotation,
            scale: 1.0,
            duration: 0.04,
            ease: "back.out(1.4)",
          }, dealStart);
        }

        // Score ring fill animation
        const ring = card.querySelector('[data-hero="score-ring"]') as SVGCircleElement | null;
        if (ring) {
          const score = parseFloat(card.querySelector(".font-bold.font-mono")?.textContent || "0");
          const targetOffset = circ * (1 - score / 10);
          tl.to(ring, {
            strokeDashoffset: targetOffset,
            duration: 0.05,
            ease: "power2.out",
          }, dealStart + 0.02);
        }
      });

      // ════════════════════════════════════════════════════════════════════
      // ACT 3: CARDS CONVERGE → SHORTS APPEAR (65% → 100%)
      // ════════════════════════════════════════════════════════════════════

      // Get the primary card's position for convergence target
      const primaryCard = cardElements[0];

      // Secondary cards fly toward primary (indices 1-4)
      if (primaryCard) {
        [1, 2, 3, 4].forEach((idx) => {
          const card = cardElements[idx];
          if (!card) return;

          tl.to(card, {
            scale: 0.3,
            autoAlpha: 0,
            duration: 0.06,
            ease: "power2.in",
          }, 0.65 + idx * 0.005);
        });

        // Primary card brief scale-up as it "absorbs" the others
        tl.to(primaryCard, {
          scale: 1.08,
          duration: 0.04,
          ease: "power2.inOut",
        }, 0.67);

        // Then settle back
        tl.to(primaryCard, {
          scale: 1.0,
          duration: 0.03,
          ease: "power2.out",
        }, 0.71);
      }

      // Hooks header fades
      const hooksHeader = content.querySelector('[data-hero="hooks-header"]') as HTMLElement;
      if (hooksHeader) {
        tl.to(hooksHeader, { autoAlpha: 0, duration: 0.03 }, 0.68);
      }

      // Hook cards section fades out, shorts section fades in
      if (hooksSection) {
        tl.to(hooksSection, { autoAlpha: 0, y: -20, duration: 0.04 }, 0.74);
      }

      // Shorts section appears
      if (shortsSection) {
        tl.to(shortsSection, { autoAlpha: 1, duration: 0.03 }, 0.77);
      }

      // Short cards deal in with stagger
      if (shortCards.length > 0) {
        gsap.set(shortCards, { autoAlpha: 0, y: 32, scale: 0.93 });

        shortCards.forEach((card, i) => {
          tl.to(card, {
            autoAlpha: 1,
            y: 0,
            scale: 1.0,
            duration: 0.05,
            ease: "back.out(1.4)",
          }, 0.79 + i * 0.03);
        });
      }

      // Specs line
      if (specs) {
        tl.to(specs, { autoAlpha: 1, duration: 0.03 }, 0.90);
      }

      // CTA
      if (cta) {
        tl.to(cta, { autoAlpha: 1, y: 0, duration: 0.04, ease: "power2.out" }, 0.93);
      }

      cleanup = () => {
        tl.kill();
        ScrollTrigger.getAll().forEach((st) => st.kill());
      };
    }

    initGSAP();
    return () => cleanup?.();
  }, [prefersReducedMotion]);

  // Reduced motion: show final state statically
  if (prefersReducedMotion) {
    return (
      <section
        className="relative bg-[#0A0A0A] overflow-hidden flex flex-col items-center justify-center px-6 pt-24 pb-20"
        style={{ minHeight: "100svh" }}
        aria-label="Hero"
      >
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: "linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px)",
              backgroundSize: "64px 64px",
            }}
          />
          <div
            className="absolute inset-0"
            style={{ background: "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(232,74,47,0.06), transparent)" }}
          />
        </div>
        <HeroSection />
      </section>
    );
  }

  return (
    <section
      ref={containerRef}
      className="relative"
      style={{ height: "400vh" }}
      aria-label="Hero"
    >
      {/* Background — covers the full scroll area */}
      <div className="absolute inset-0 bg-[#0A0A0A] pointer-events-none" aria-hidden="true">
        <div
          className="sticky top-0 h-screen"
          style={{
            backgroundImage: "linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
          }}
        />
      </div>
      <div
        className="absolute inset-0 pointer-events-none"
        aria-hidden="true"
      >
        <div
          className="sticky top-0 h-screen"
          style={{ background: "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(232,74,47,0.06), transparent)" }}
        />
      </div>

      {/* Sticky viewport — pinned while scrolling */}
      <div
        className="flex items-center justify-center px-6 pt-24 pb-20 overflow-hidden"
        style={{
          position: "sticky",
          top: 0,
          height: "100vh",
          minHeight: "600px",
        }}
      >
        <div ref={contentRef}>
          <HeroSection />
        </div>
      </div>
    </section>
  );
}
