"use client";

import { useState } from "react";
import Link from "next/link";
import { HeroSection } from "./hero-section";
import {
  Target,
  Globe,
  Ban,
  Lightbulb,
  Smartphone,
  Zap,
  Scissors,
  BarChart3,
  Type,
  Users,
} from "lucide-react";
import { PLANS, detectCurrency } from "@/lib/pricing-data";

// ── How it works ────────────────────────────────────────────────────────────

const STEPS = [
  {
    n: "01",
    title: "Paste a YouTube URL",
    desc: "Podcast, tutorial, vlog, interview — any length, any language. Just drop the link.",
    icon: Zap,
  },
  {
    n: "02",
    title: "AI scores 5 hook moments",
    desc: "Each moment is ranked across 7 dimensions — curiosity, emotion, authority, and more. You see the score and the reasoning.",
    icon: BarChart3,
  },
  {
    n: "03",
    title: "Export ready-to-post Shorts",
    desc: "Pick your hooks, choose a caption style, trim boundaries, and download 9:16 clips with captions burned in.",
    icon: Scissors,
  },
] as const;

// ── Features ────────────────────────────────────────────────────────────────

const FEATURES = [
  {
    icon: Target,
    title: "7-dimension hook scoring",
    desc: "Every moment is ranked on curiosity, emotion, authority, specificity, controversy, relatability, and pattern interrupt.",
    accent: "#E84A2F",
  },
  {
    icon: Globe,
    title: "12 languages, auto-detected",
    desc: "Hindi, Tamil, Telugu, Bengali, Spanish, and more. No language dropdown — we detect it automatically.",
    accent: "#3B82F6",
  },
  {
    icon: Ban,
    title: "Filler never makes the cut",
    desc: "Intros, sponsor reads, \"smash that like button\" — all filtered before scoring even starts.",
    accent: "#F59E0B",
  },
  {
    icon: Lightbulb,
    title: "Creator insights on every hook",
    desc: "Platform dynamics, viewer psychology analysis, and actionable creator tips you can apply to your next video.",
    accent: "#8B5CF6",
  },
  {
    icon: Type,
    title: "4 caption styles",
    desc: "Clean, Bold, Neon, or Minimal — captions are burned directly into the video, ready for any platform.",
    accent: "#EC4899",
  },
  {
    icon: Users,
    title: "Interview mode",
    desc: "Multi-speaker diarization with split-screen Shorts. Perfect for podcasts, panels, and conversations.",
    accent: "#14B8A6",
  },
  {
    icon: Smartphone,
    title: "Multiple aspect ratios",
    desc: "Export as 9:16 for Shorts/Reels/TikTok, 1:1 for Instagram feed, or 4:5 for LinkedIn.",
    accent: "#F97316",
  },
  {
    icon: Scissors,
    title: "Trim boundaries ±10s",
    desc: "Fine-tune the start and end of each hook. Preview the exact segment before generating your Short.",
    accent: "#06B6D4",
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
  const [annual, setAnnual] = useState(false);
  const [currency] = useState<"INR" | "USD">(detectCurrency);

  return (
    <div>
      {/* ── 1. HERO ── */}
      <HeroSection />

      {/* ── 2. HOW IT WORKS ── */}
      <section className="bg-[#0F0F0F] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
              How It Works
            </p>
            <h2 className="text-[clamp(28px,4vw,48px)] font-extrabold text-white/90 tracking-[-0.03em] font-[family-name:--font-display]">
              URL in, viral Shorts out.
            </h2>
            <p className="text-white/30 text-sm mt-2">
              Paste a YouTube link. Get 5 hook-scored clips in under 2 minutes —
              no editing skills needed.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {STEPS.map((step, i) => (
              <div key={step.n} className="relative">
                {/* Connector line */}
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-[calc(100%+1rem)] w-[calc(100%-2rem)] h-px">
                    <div className="w-full h-full border-t border-dashed border-white/[0.08]" />
                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-white/[0.08]" />
                  </div>
                )}

                <div className="glass-card rounded-xl p-6 h-full">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-[#E84A2F]/10 border border-[#E84A2F]/15 flex items-center justify-center">
                      <step.icon className="w-5 h-5 text-[#E84A2F]" strokeWidth={1.5} />
                    </div>
                    <span className="text-[32px] font-extrabold text-[#E84A2F]/15 font-mono leading-none">
                      {step.n}
                    </span>
                  </div>
                  <h3 className="text-white/90 font-bold text-lg mb-2">
                    {step.title}
                  </h3>
                  <p className="text-white/45 text-sm leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 3. FEATURES ── */}
      <section id="features" className="bg-[var(--color-surface-1)] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
              Features
            </p>
            <h2 className="text-[clamp(28px,4vw,48px)] font-extrabold text-white/90 tracking-[-0.03em] font-[family-name:--font-display]">
              The only AI built to find hooks, not just clips.
            </h2>
            <p className="text-white/30 text-sm mt-2">
              Other tools clip randomly. HookCut scores every moment for
              virality, emotion, and platform fit — then cuts the winners.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURES.map((feat) => (
              <div
                key={feat.title}
                className="glass-card rounded-xl p-5 glass-hover group"
              >
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center mb-3"
                  style={{ background: `${feat.accent}12`, border: `1px solid ${feat.accent}20` }}
                >
                  <feat.icon
                    className="w-[18px] h-[18px]"
                    style={{ color: feat.accent }}
                    strokeWidth={1.5}
                  />
                </div>
                <h3 className="text-white/90 font-semibold text-[14px] mb-1.5">
                  {feat.title}
                </h3>
                <p className="text-white/40 text-[13px] leading-relaxed">
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
              Start free. Scale when you&apos;re ready.
            </h2>
            <p className="text-white/25 text-sm mt-3">
              No billing surprises. If a job fails, your credits come back.
            </p>

            {/* Annual/Monthly toggle */}
            <div className="flex items-center justify-center gap-3 mt-6">
              <button
                type="button"
                onClick={() => setAnnual(false)}
                className={`text-sm font-medium px-4 py-1.5 rounded-full transition-colors ${
                  !annual
                    ? "bg-white/[0.1] text-white"
                    : "text-white/40 hover:text-white/60"
                }`}
              >
                Monthly
              </button>
              <button
                type="button"
                onClick={() => setAnnual(true)}
                className={`text-sm font-medium px-4 py-1.5 rounded-full transition-colors ${
                  annual
                    ? "bg-white/[0.1] text-white"
                    : "text-white/40 hover:text-white/60"
                }`}
              >
                Annual{" "}
                <span className="text-[#E84A2F] text-xs font-semibold">
                  (Save 20%)
                </span>
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-2xl mx-auto">
            {PLANS.map((plan) => {
              const isHighlighted = plan.highlighted;
              const monthlyPrice =
                currency === "INR" ? plan.priceINR : plan.priceUSD;
              const annualPrice = Math.round(monthlyPrice * 0.8);
              const displayPrice =
                annual && monthlyPrice > 0 ? annualPrice : monthlyPrice;
              const sym = currency === "INR" ? "\u20B9" : "$";

              return (
                <div
                  key={plan.key}
                  className={`rounded-xl p-6 flex flex-col ${
                    isHighlighted
                      ? "bg-[#E84A2F]"
                      : "border border-white/[0.06] bg-white/[0.02]"
                  }`}
                >
                  <div className="mb-6">
                    <p
                      className={`text-xs font-semibold uppercase tracking-wider mb-1 ${
                        isHighlighted ? "text-white/60" : "text-white/30"
                      }`}
                    >
                      {plan.name}
                    </p>
                    <p className="text-white text-3xl font-bold font-mono">
                      {plan.period ? (
                        <>
                          {sym}
                          {displayPrice}
                          <span
                            className={`text-base font-normal ${
                              isHighlighted
                                ? "text-white/60"
                                : "text-white/25"
                            }`}
                          >
                            /mo
                          </span>
                        </>
                      ) : (
                        <>Free</>
                      )}
                    </p>
                    {annual && monthlyPrice > 0 && (
                      <p
                        className={`text-sm line-through ${
                          isHighlighted ? "text-white/50" : "text-white/40"
                        }`}
                      >
                        {sym}
                        {monthlyPrice}/mo
                      </p>
                    )}
                    <p
                      className={`text-sm ${
                        isHighlighted ? "text-white/60" : "text-white/25"
                      }`}
                    >
                      {plan.period
                        ? `${plan.aiMinutes} AI min/mo`
                        : `${plan.aiMinutes} AI min included`}
                    </p>
                  </div>
                  <ul className="space-y-2.5 flex-1 mb-6">
                    {plan.features.map((f) => (
                      <li
                        key={f}
                        className={`flex items-center gap-2.5 text-sm ${
                          isHighlighted ? "text-white/80" : "text-white/60"
                        }`}
                      >
                        <Check white={isHighlighted} />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Link
                    href={plan.key === "free" ? "/auth/login" : "/pricing"}
                    className={`block w-full py-2.5 rounded-lg text-sm font-semibold text-center transition-colors ${
                      isHighlighted
                        ? "bg-white text-[#E84A2F] hover:bg-white/90"
                        : "bg-white/[0.06] text-white/50 hover:bg-white/[0.1]"
                    }`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              );
            })}
          </div>

          {/* Pay-as-you-go */}
          <div className="mt-6 max-w-3xl mx-auto rounded-xl border border-white/[0.06] bg-white/[0.02] px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-white/70 text-sm font-semibold">
                Need more minutes?
              </p>
              <p className="text-white/30 text-sm">
                Top up anytime — no subscription required.
              </p>
            </div>
            <Link
              href="/pricing"
              className="shrink-0 px-5 py-2 rounded-lg text-sm font-semibold bg-white/[0.06] text-white/50 hover:bg-white/[0.1] transition-colors"
            >
              Buy Minutes
            </Link>
          </div>

          {/* Guarantee strip */}
          <p className="text-center text-white/25 text-xs mt-6">
            30-day money-back guarantee &middot; No questions asked &middot;
            Credits refunded if analysis fails
          </p>
        </div>
      </section>

      {/* ── 5. FINAL CTA ── */}
      <section className="bg-[#0A0A0A] border-t border-white/[0.04] py-28 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-[clamp(28px,4.5vw,52px)] font-extrabold text-white mb-4 tracking-[-0.035em] leading-[1.1] font-[family-name:--font-display]">
            Your next viral Short is hiding in a video you already made.
          </h2>
          <p className="text-white/25 text-base mb-10">
            AI finds it in under 2 minutes. No editing skills required. Free to
            try.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
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
            <Link
              href="#features"
              className="inline-flex items-center gap-2 btn-secondary px-8 py-3.5 rounded-full text-sm font-semibold"
            >
              See All Features
            </Link>
          </div>
          <p className="text-white/15 text-xs mt-3">
            120 minutes free &middot; No credit card required
          </p>
        </div>
      </section>
    </div>
  );
}
