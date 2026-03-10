"use client";

import { useState } from "react";
import Link from "next/link";
import { HeroSection } from "./hero-section";
import { Target, Globe, Ban, Lightbulb, Smartphone, Wallet } from "lucide-react";
import { PLANS, detectCurrency } from "@/lib/pricing-data";

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
  const [annual, setAnnual] = useState(false);
  const [currency] = useState<"INR" | "USD">(detectCurrency);

  return (
    <div>
      {/* ── 1. HERO ── */}
      <HeroSection />

      {/* ── 2. HOW IT WORKS ── */}
      <section className="bg-[#0F0F0F] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            How It Works
          </p>
          <h2 className="text-[clamp(28px,4vw,48px)] font-extrabold text-white/90 tracking-[-0.03em] mb-2 font-[family-name:--font-display]">
            URL in, Shorts out.
          </h2>
          <p className="text-white/30 text-sm mb-16">
            (Most creators get their first Short in under 3 minutes)
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative">
            {STEPS.map((step, i) => (
              <div key={step.n} className="flex flex-col gap-4 relative">
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-6 left-full w-full border-t border-dashed border-white/[0.08]" />
                )}
                <span className="text-[48px] font-extrabold text-[#E84A2F]/20 font-mono leading-none tracking-[-0.05em]">
                  {step.n}
                </span>
                <h3 className="text-white/90 font-bold text-lg">{step.title}</h3>
                <p className="text-white/50 text-sm leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 3. FEATURES ── */}
      <section id="features" className="bg-[var(--color-surface-1)] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            Features
          </p>
          <h2 className="text-[clamp(28px,4vw,48px)] font-extrabold text-white/90 tracking-[-0.03em] mb-14 font-[family-name:--font-display]">
            Every clip comes with a reason.
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((feat) => (
              <div
                key={feat.title}
                className="glass-card rounded-xl p-6 glass-hover"
              >
                <feat.icon
                  className="w-6 h-6 text-[#E84A2F] mb-4"
                  strokeWidth={1.5}
                />
                <h3 className="text-white/90 font-semibold text-[15px] mb-2">
                  {feat.title}
                </h3>
                <p className="text-white/50 text-sm leading-relaxed">
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
                onClick={() => setAnnual(true)}
                className={`text-sm font-medium px-4 py-1.5 rounded-full transition-colors ${
                  annual
                    ? "bg-white/[0.1] text-white"
                    : "text-white/40 hover:text-white/60"
                }`}
              >
                Annual <span className="text-[#E84A2F] text-xs font-semibold">(Save 20%)</span>
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-3xl mx-auto">
            {PLANS.map((plan) => {
              const isHighlighted = plan.highlighted;
              const monthlyPrice = currency === "INR" ? plan.priceINR : plan.priceUSD;
              const annualPrice = Math.round(monthlyPrice * 0.8);
              const displayPrice = annual && monthlyPrice > 0 ? annualPrice : monthlyPrice;
              const sym = currency === "INR" ? "₹" : "$";

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
                      {plan.period
                        ? <>{sym}{displayPrice}<span className={`text-base font-normal ${isHighlighted ? "text-white/60" : "text-white/25"}`}>/mo</span></>
                        : <>Free</>
                      }
                    </p>
                    {annual && monthlyPrice > 0 && (
                      <p className={`text-sm line-through ${isHighlighted ? "text-white/50" : "text-white/40"}`}>
                        {sym}{monthlyPrice}/mo
                      </p>
                    )}
                    <p className={`text-sm ${isHighlighted ? "text-white/60" : "text-white/25"}`}>
                      {plan.period ? `${plan.minutes} min of video` : `${plan.minutes} min included`}
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
                        : plan.key === "pro"
                          ? "bg-[#E84A2F] text-white hover:bg-[#D13F25]"
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
              <p className="text-white/70 text-sm font-semibold">Need more minutes?</p>
              <p className="text-white/30 text-sm">Top up anytime — no subscription required.</p>
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
            30-day money-back guarantee &middot; No questions asked &middot; Credits refunded if analysis fails
          </p>
        </div>
      </section>

      {/* ── 6. FINAL CTA ── */}
      {/* MarketingHome only renders for unauthenticated users (see HomeStateMachine),
          so CTA links to /auth/login are intentional. */}
      <section className="bg-[#0A0A0A] border-t border-white/[0.04] py-32 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-[clamp(28px,4.5vw,52px)] font-extrabold text-white mb-4 tracking-[-0.035em] leading-[1.1] font-[family-name:--font-display]">
            Your best Short is hiding in a video you already made.
          </h2>
          <p className="text-white/25 text-base mb-10">
            Find it in 90 seconds. No editing skills required.
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
              href="/how-it-works"
              className="inline-flex items-center gap-2 btn-secondary px-8 py-3.5 rounded-full text-sm font-semibold"
            >
              See How It Works
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
