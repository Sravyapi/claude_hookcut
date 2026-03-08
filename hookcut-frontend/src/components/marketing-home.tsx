"use client";

import Link from "next/link";
import { HeroSection } from "./hero-section";
import { Target, Globe, Ban, Lightbulb, Smartphone, Wallet } from "lucide-react";

// ── How it works ────────────────────────────────────────────────────────────

const STEPS = [
  {
    n: "01",
    title: "Drop a YouTube link",
    desc: "Podcast, tutorial, vlog — any length, any language. Just paste the URL.",
  },
  {
    n: "02",
    title: "See why each moment works",
    desc: "AI scores 5 hooks across 7 dimensions and tells you exactly what makes each one stop the scroll.",
  },
  {
    n: "03",
    title: "Export ready-to-post Shorts",
    desc: "Pick your hooks, choose a caption style, download 9:16 clips with captions burned in.",
  },
] as const;

// ── Features ────────────────────────────────────────────────────────────────

const FEATURES = [
  {
    icon: Target,
    title: "Hook scoring, not guessing",
    desc: "Every moment is ranked across 7 dimensions — curiosity, emotion, authority, and more. You see the score and the reason.",
  },
  {
    icon: Globe,
    title: "Works in 12 languages",
    desc: "Hindi, Tamil, Telugu, Bengali, Spanish, and more. Language is auto-detected — no setup needed.",
  },
  {
    icon: Ban,
    title: "Filler never makes the cut",
    desc: 'Intros, sponsor reads, "smash that like button" — all filtered out before scoring even starts.',
  },
  {
    icon: Lightbulb,
    title: "Learn why hooks work",
    desc: "Every result includes platform dynamics, viewer psychology, and a creator tip you can apply to your next video.",
  },
  {
    icon: Smartphone,
    title: "Post-ready in minutes",
    desc: "Choose your hooks, pick a caption style, download vertical clips with captions already burned in.",
  },
  {
    icon: Wallet,
    title: "Priced for Indian creators",
    desc: "UPI, cards, and wallets accepted. Starts at \u20B9499/month — no dollar conversion, no surprises.",
  },
] as const;

// ── Checkmark icon ──────────────────────────────────────────────────────────

function Check({ white }: { white?: boolean }) {
  return (
    <svg
      className={`w-4 h-4 shrink-0 ${white ? "text-white" : "text-[#E84A2F]"}`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2.5}
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}

// ── Main export ─────────────────────────────────────────────────────────────

export function MarketingHome() {
  return (
    <div>
      {/* ── 1. HERO ── */}
      <HeroSection />

      {/* ── 2. HOW IT WORKS ── */}
      <section className="bg-[#FAFAF8] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            How It Works
          </p>
          <h2 className="text-[clamp(28px,4vw,48px)] font-extrabold text-[#111] tracking-[-0.03em] mb-16 font-[family-name:--font-display]">
            URL in, Shorts out.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {STEPS.map((step) => (
              <div key={step.n} className="flex flex-col gap-4">
                <span className="text-[48px] font-extrabold text-[#E84A2F]/15 font-mono leading-none tracking-[-0.05em]">
                  {step.n}
                </span>
                <h3 className="text-[#111] font-bold text-lg">{step.title}</h3>
                <p className="text-[#71717A] text-sm leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 3. FEATURES ── */}
      <section id="features" className="bg-[#F5F5F3] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            Features
          </p>
          <h2 className="text-[clamp(28px,4vw,48px)] font-extrabold text-[#111] tracking-[-0.03em] mb-14 font-[family-name:--font-display]">
            Every clip comes with a reason.
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((feat) => (
              <div
                key={feat.title}
                className="bg-white border border-[#E4E4E7] rounded-xl p-6"
              >
                <feat.icon
                  className="w-5 h-5 text-[#E84A2F] mb-4"
                  strokeWidth={1.5}
                />
                <h3 className="text-[#111] font-semibold text-[15px] mb-2">
                  {feat.title}
                </h3>
                <p className="text-[#71717A] text-sm leading-relaxed">
                  {feat.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 4. PRICING ── */}
      <section id="pricing" className="bg-[#111] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
              Pricing
            </p>
            <h2 className="text-[clamp(28px,4vw,48px)] font-extrabold text-white tracking-[-0.03em] font-[family-name:--font-display]">
              Start free. Scale when you're ready.
            </h2>
            <p className="text-white/25 text-sm mt-3">
              No billing surprises. If a job fails, your credits come back.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-3xl mx-auto">
            {/* Free */}
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6 flex flex-col">
              <div className="mb-6">
                <p className="text-white/30 text-xs font-semibold uppercase tracking-wider mb-1">
                  Free
                </p>
                <p className="text-white text-3xl font-bold font-mono">{"\u20B9"}0</p>
                <p className="text-white/25 text-sm">120 min included</p>
              </div>
              <ul className="space-y-2.5 flex-1 mb-6">
                {["5 hooks per video", "3 Shorts per video", "Watermarked"].map(
                  (f) => (
                    <li
                      key={f}
                      className="flex items-center gap-2.5 text-sm text-white/40"
                    >
                      <Check />
                      {f}
                    </li>
                  ),
                )}
              </ul>
              <Link
                href="/auth/login"
                className="block w-full py-2.5 rounded-lg text-sm font-semibold text-center bg-white/[0.06] text-white/50 hover:bg-white/[0.1] transition-colors"
              >
                Start Free
              </Link>
            </div>

            {/* Starter — highlighted */}
            <div className="rounded-xl bg-[#E84A2F] p-6 flex flex-col">
              <div className="mb-6">
                <p className="text-white/60 text-xs font-semibold uppercase tracking-wider mb-1">
                  Starter
                </p>
                <p className="text-white text-3xl font-bold font-mono">{"\u20B9"}499<span className="text-base font-normal text-white/60">/mo</span></p>
                <p className="text-white/60 text-sm">200 min of video</p>
              </div>
              <ul className="space-y-2.5 flex-1 mb-6">
                {[
                  "5 hooks per video",
                  "3 Shorts per video",
                  "No watermark",
                  "Priority queue",
                ].map((f) => (
                  <li
                    key={f}
                    className="flex items-center gap-2.5 text-sm text-white/80"
                  >
                    <Check white />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/pricing"
                className="block w-full py-2.5 rounded-lg text-sm font-semibold text-center bg-white text-[#E84A2F] hover:bg-white/90 transition-colors"
              >
                Get Started
              </Link>
            </div>

            {/* Pro */}
            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-6 flex flex-col">
              <div className="mb-6">
                <p className="text-white/30 text-xs font-semibold uppercase tracking-wider mb-1">
                  Pro
                </p>
                <p className="text-white text-3xl font-bold font-mono">{"\u20B9"}999<span className="text-base font-normal text-white/25">/mo</span></p>
                <p className="text-white/25 text-sm">500 min of video</p>
              </div>
              <ul className="space-y-2.5 flex-1 mb-6">
                {[
                  "5 hooks per video",
                  "3 Shorts per video",
                  "No watermark",
                  "Priority support",
                ].map((f) => (
                  <li
                    key={f}
                    className="flex items-center gap-2.5 text-sm text-white/40"
                  >
                    <Check />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/pricing"
                className="block w-full py-2.5 rounded-lg text-sm font-semibold text-center bg-[#E84A2F] text-white hover:bg-[#D13F25] transition-colors"
              >
                Go Pro
              </Link>
            </div>
          </div>

          {/* Pay-as-you-go */}
          <div className="mt-6 max-w-3xl mx-auto rounded-xl border border-white/[0.06] bg-white/[0.02] px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-white/70 text-sm font-semibold">Need more minutes?</p>
              <p className="text-white/30 text-sm">Top up anytime at {"\u20B9"}5/min — no subscription required.</p>
            </div>
            <Link
              href="/pricing"
              className="shrink-0 px-5 py-2 rounded-lg text-sm font-semibold bg-white/[0.06] text-white/50 hover:bg-white/[0.1] transition-colors"
            >
              Buy Minutes
            </Link>
          </div>
        </div>
      </section>

      {/* ── 6. FINAL CTA ── */}
      <section className="bg-[#0A0A0A] border-t border-white/[0.04] py-24 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-[clamp(28px,4.5vw,52px)] font-extrabold text-white mb-4 tracking-[-0.035em] leading-[1.1] font-[family-name:--font-display]">
            Your best Short is hiding in a video you already made.
          </h2>
          <p className="text-white/25 text-base mb-10">
            Find it in 90 seconds. No editing skills required.
          </p>
          <Link
            href="/auth/login"
            className="inline-flex items-center gap-2 btn-primary px-8 py-3.5 rounded-full text-sm font-semibold"
          >
            Start Analyzing Free
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </Link>
          <p className="text-white/15 text-xs mt-3">
            120 minutes free &middot; No credit card required
          </p>
        </div>
      </section>
    </div>
  );
}
