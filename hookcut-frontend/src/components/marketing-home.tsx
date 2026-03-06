import Link from "next/link";
import { HeroSection } from "./hero-section";
import { DEMO_HOOKS } from "@/lib/constants";

// ── Ticker items ───────────────────────────────────────────────────────────────

const TICKER_ITEMS = [
  "Results in under 2 minutes",
  "120 free minutes on signup",
  "No credit card required",
  "18 hook types detected",
  "7-dimension AI scoring",
  "12 languages supported",
  "Auto-rejects filler & sponsors",
  "9:16 Shorts, captions burned in",
] as const;

// ── Icon helpers ───────────────────────────────────────────────────────────────

function CheckIcon() {
  return (
    <svg
      className="w-4 h-4 text-[#E84A2F] shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg
      className="w-4 h-4 text-red-400/50 shrink-0"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  );
}

// ── Pricing card ───────────────────────────────────────────────────────────────

function PriceCard({
  name,
  price,
  priceINR,
  credits,
  features,
  highlighted,
  cta,
  href,
}: {
  name: string;
  price: string;
  priceINR: string;
  credits: string;
  features: readonly string[];
  highlighted?: boolean;
  cta: string;
  href: string;
}) {
  return (
    <div
      className={`rounded-2xl p-6 flex flex-col gap-4 ${
        highlighted
          ? "bg-[#E84A2F] text-white"
          : "bg-[#141414] border border-white/[0.08]"
      }`}
    >
      <div>
        <div
          className={`text-xs font-semibold uppercase tracking-wider mb-1 ${
            highlighted ? "text-white/70" : "text-white/30"
          }`}
        >
          {name}
        </div>
        <div
          className={`text-3xl font-bold font-mono ${
            highlighted ? "text-white" : "text-white/90"
          }`}
        >
          {price}
        </div>
        <div className={`text-sm ${highlighted ? "text-white/70" : "text-white/30"}`}>
          {priceINR} · {credits}
        </div>
      </div>
      <ul className="space-y-2.5 flex-1">
        {features.map((f) => (
          <li
            key={f}
            className={`flex items-center gap-2.5 text-sm ${
              highlighted ? "text-white/90" : "text-white/50"
            }`}
          >
            <svg
              className={`w-4 h-4 shrink-0 ${highlighted ? "text-white" : "text-[#E84A2F]"}`}
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
            {f}
          </li>
        ))}
      </ul>
      <Link
        href={href}
        className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-colors text-center block ${
          highlighted
            ? "bg-white text-[#E84A2F] hover:bg-white/90"
            : "bg-[#E84A2F] text-white hover:bg-[#D13F25]"
        }`}
      >
        {cta}
      </Link>
    </div>
  );
}

// ── Main export ────────────────────────────────────────────────────────────────

export function MarketingHome() {
  return (
    <div>
      {/* ── 1. HERO ── */}
      <HeroSection />

      {/* ── 2. MARQUEE ── */}
      <div className="bg-[#111] border-y border-white/[0.05] py-3.5 overflow-hidden">
        <div className="mk-ticker gap-14 whitespace-nowrap">
          {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
            <span
              key={i}
              className="text-white/30 text-xs font-medium shrink-0 tracking-wide"
            >
              {item}
              <span className="mx-8 text-white/[0.1]" aria-hidden="true">·</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── 3. STATEMENT ── */}
      <section className="bg-[#FAFAF8] py-28 px-6 overflow-hidden">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-8">
            The problem
          </p>
          <div className="flex flex-col leading-none">
            <span
              className="text-[#111] font-extrabold tracking-[-0.04em] font-[family-name:--font-display]"
              style={{ fontSize: "clamp(48px,7vw,108px)", lineHeight: 0.95 }}
            >
              The first
            </span>
            <span
              className="text-[#E84A2F] font-extrabold tracking-[-0.04em] font-[family-name:--font-display]"
              style={{ fontSize: "clamp(80px,13vw,192px)", lineHeight: 0.88 }}
            >
              2 secs
            </span>
            <span
              className="text-[#111] font-extrabold tracking-[-0.04em] font-[family-name:--font-display]"
              style={{ fontSize: "clamp(48px,7vw,108px)", lineHeight: 0.95 }}
            >
              decide everything.
            </span>
          </div>
          <p className="mt-12 text-[#71717A] text-lg leading-relaxed max-w-lg">
            Most viewers scroll past a video in under 2 seconds. The difference between 10
            views and 10 million isn&apos;t production quality — it&apos;s the first line.
            HookCut finds that line in your video.
          </p>
        </div>
      </section>

      {/* ── 4. HOW IT WORKS ── */}
      <section id="features" className="bg-[#F5F5F3] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            How It Works
          </p>
          <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-[#111] tracking-[-0.03em] mb-16 font-[family-name:--font-display]">
            Three steps.
            <br />
            One viral Short.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {(
              [
                {
                  n: "01",
                  title: "Paste your YouTube URL",
                  desc: "Any video, any length, any language. Podcasts, tutorials, vlogs — all supported.",
                },
                {
                  n: "02",
                  title: "AI surfaces the hook moments",
                  desc: "HookCut scores every moment in your video and surfaces the 5 most likely to go viral — each one explained.",
                },
                {
                  n: "03",
                  title: "Download your Shorts",
                  desc: "Ready-to-post 9:16 clips with captions. No editing software. No guesswork.",
                },
              ] as const
            ).map((step) => (
              <div key={step.n} className="flex flex-col gap-4">
                <span className="text-[56px] font-extrabold text-[#E84A2F] font-mono leading-none tracking-[-0.05em]">
                  {step.n}
                </span>
                <div className="h-px w-8 bg-[#E84A2F]/30" />
                <h3 className="text-[#111] font-bold text-lg">{step.title}</h3>
                <p className="text-[#71717A] text-sm leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 5. HOOK SHOWCASE ── */}
      <section className="bg-[#FAFAF8] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            Hook Intelligence
          </p>
          <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-[#111] tracking-[-0.03em] mb-4 font-[family-name:--font-display]">
            Every moment scored.
            <br />
            Only the best ones ship.
          </h2>
          <p className="text-[#71717A] text-base mb-14 max-w-lg">
            HookCut intelligently rejects filler, greetings, and sponsor segments. What
            remains: the moments most likely to stop a scroll.
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 lg:items-start">
            {DEMO_HOOKS.map((hook, i) => {
              const offsets = ["lg:mt-0", "lg:mt-10", "lg:mt-5"];
              const circumference = 2 * Math.PI * 28;
              const strokeOffset = circumference - (hook.score / 10) * circumference;
              return (
                <div
                  key={hook.type}
                  className={`rounded-2xl border border-[#E4E4E7] bg-white p-6 flex flex-col gap-4 shadow-sm ${offsets[i]}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="relative w-16 h-16 shrink-0">
                      <svg
                        viewBox="0 0 64 64"
                        className="w-full h-full -rotate-90"
                        aria-hidden="true"
                      >
                        <circle
                          cx="32"
                          cy="32"
                          r="28"
                          fill="none"
                          stroke="#F4F4F5"
                          strokeWidth="4"
                        />
                        <circle
                          cx="32"
                          cy="32"
                          r="28"
                          fill="none"
                          stroke={hook.color}
                          strokeWidth="4"
                          strokeLinecap="round"
                          strokeDasharray={circumference}
                          strokeDashoffset={strokeOffset}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="font-mono font-bold text-[#111] text-base">
                          {hook.score}
                        </span>
                      </div>
                    </div>
                    <div>
                      <span
                        className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full"
                        style={{
                          color: hook.color,
                          background: `${hook.color}18`,
                          border: `1px solid ${hook.color}30`,
                        }}
                      >
                        {hook.type}
                      </span>
                      <p className="text-[11px] text-[#A1A1AA] font-mono mt-2">
                        {hook.timestamp}
                      </p>
                    </div>
                  </div>
                  <p className="text-[13px] text-[#0A0A0A]/60 leading-relaxed">{hook.text}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── 6. COMPARISON ── */}
      <section className="bg-[#F5F5F3] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            Why HookCut
          </p>
          <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-[#111] tracking-[-0.03em] mb-12 font-[family-name:--font-display]">
            What nobody else does.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-14">
            <div className="rounded-2xl bg-[#EBEBEB] p-6">
              <p className="text-[#71717A] text-xs font-semibold uppercase tracking-wider mb-5">
                Other AI Clippers
              </p>
              <ul className="space-y-3">
                {(
                  [
                    "Cut at every sentence, good or bad",
                    "Include greeting clips and filler",
                    "Give you 40 clips to sort through",
                    "No explanation of why clips were chosen",
                    "$29–$79/month, billed in USD",
                  ] as const
                ).map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm text-[#71717A]">
                    <XIcon />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl bg-white border border-[#E84A2F]/15 p-6 shadow-sm">
              <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-wider mb-5">
                HookCut
              </p>
              <ul className="space-y-3">
                {(
                  [
                    "Scores every moment, only ships the best",
                    "Actively rejects greetings and sponsors",
                    "Surfaces 5 high-quality hook segments",
                    "Explains why each moment is scroll-stopping",
                    "From $7/month · UPI accepted",
                  ] as const
                ).map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm text-[#111]/80">
                    <CheckIcon />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="overflow-x-auto rounded-2xl border border-[#E4E4E7] bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E4E4E7]">
                  <th className="text-left p-4 text-[#71717A] font-medium w-44">Feature</th>
                  <th className="p-4 text-[#E84A2F] font-bold text-center">HookCut</th>
                  <th className="p-4 text-[#71717A] font-medium text-center">OpusClip</th>
                  <th className="p-4 text-[#71717A] font-medium text-center">Klap</th>
                  <th className="p-4 text-[#71717A] font-medium text-center">Vizard</th>
                </tr>
              </thead>
              <tbody>
                {(
                  [
                    ["Hook Score (0–10)", "✓", "✗", "✗", "✗"],
                    ["Explains why each clip was chosen", "✓", "✗", "✗", "✗"],
                    ["Rejects filler clips automatically", "✓", "✗", "✗", "✗"],
                    ["Price / month (USD)", "$7", "$29+", "$17+", "$19+"],
                    ["India pricing (INR + UPI)", "✓", "✗", "✗", "✗"],
                    ["Cancel anytime", "✓", "✓", "✓", "✓"],
                  ] as const
                ).map(([feature, hookcut, opus, klap, vizard], i) => (
                  <tr key={feature} className={i % 2 === 0 ? "bg-white" : "bg-[#FAFAF8]"}>
                    <td className="p-4 text-[#0A0A0A]/70 font-medium">{feature}</td>
                    <td className="p-4 text-center font-semibold text-[#E84A2F]">{hookcut}</td>
                    <td className="p-4 text-center text-[#71717A]">{opus}</td>
                    <td className="p-4 text-center text-[#71717A]">{klap}</td>
                    <td className="p-4 text-center text-[#71717A]">{vizard}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── 7. FEATURE HIGHLIGHTS ── */}
      <section className="bg-[#FAFAF8] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
            What makes it different
          </p>
          <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-[#111] tracking-[-0.03em] mb-14 font-[family-name:--font-display]">
            Not a clipper.
            <br />
            A hook engine.
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {(
              [
                {
                  icon: "🎯",
                  title: "18 hook types, scored",
                  desc: "Curiosity gaps, pattern interrupts, bold claims, social proof — every type identified and ranked by a 7-dimension scoring model.",
                },
                {
                  icon: "🌐",
                  title: "12 languages, zero setup",
                  desc: "Hindi, Tamil, Telugu, Bengali, Kannada, Malayalam, Punjabi, Marathi, Gujarati, and more — auto-detected, no dropdown.",
                },
                {
                  icon: "🚫",
                  title: "Auto-rejects filler",
                  desc: "Greetings, \"smash that like button\", sponsor reads — filtered out before scoring. Only real content gets evaluated.",
                },
                {
                  icon: "🧠",
                  title: "Explains the why",
                  desc: "Each hook comes with platform dynamics, viewer psychology, and a creator tip — not just a timestamp.",
                },
                {
                  icon: "📐",
                  title: "9:16 ready in minutes",
                  desc: "Select your hooks, pick a caption style, get back a download-ready MP4 with burned-in captions. No editing software needed.",
                },
                {
                  icon: "💳",
                  title: "Pay in rupees",
                  desc: "UPI, cards, wallets accepted. ₹499/month for Lite — no dollar conversion, no currency surprises.",
                },
              ] as const
            ).map((feat) => (
              <div
                key={feat.title}
                className="bg-white border border-[#E4E4E7] rounded-2xl p-6 shadow-sm"
              >
                <div className="text-2xl mb-4" aria-hidden="true">{feat.icon}</div>
                <h3 className="text-[#111] font-bold text-base mb-2">{feat.title}</h3>
                <p className="text-[#71717A] text-sm leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 8. INDIA ── */}
      <section className="bg-[#F5F5F3] py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-[clamp(24px,3.5vw,44px)] font-extrabold text-[#111] mb-4 tracking-[-0.03em] font-[family-name:--font-display]">
            Built for creators across India.
          </h2>
          <p className="text-[#71717A] text-base leading-relaxed mb-8">
            Pay in rupees. Analyze Hinglish content. ₹499/month — no dollar conversion
            surprises.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {(
              [
                "🇮🇳  ₹499/month",
                "UPI accepted",
                "12+ Indian languages",
                "Hinglish supported",
              ] as const
            ).map((pill) => (
              <span
                key={pill}
                className="px-4 py-2 rounded-full bg-white border border-[#E4E4E7] text-[#111] text-sm font-medium shadow-sm"
              >
                {pill}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── 9. PRICING ── */}
      <section id="pricing" className="bg-[#0A0A0A] py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">
              Pricing
            </p>
            <h2 className="text-[clamp(28px,4vw,52px)] font-extrabold text-white tracking-[-0.03em] font-[family-name:--font-display]">
              Simple, honest pricing.
            </h2>
            <p className="text-white/30 text-sm mt-3">
              No billing surprises. Credits refunded on analysis failures.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <PriceCard
              name="Free"
              price="$0"
              priceINR="₹0"
              credits="120 min included"
              features={["5 hooks per video", "3 Shorts per batch", "Watermarked clips"]}
              cta="Start Free"
              href="/auth/login"
            />
            <PriceCard
              name="Lite"
              price="$7"
              priceINR="₹499/mo"
              credits="100 min/month"
              features={[
                "5 hooks per video",
                "10 Shorts per batch",
                "No watermark",
                "Priority queue",
              ]}
              highlighted
              cta="Start Analyzing →"
              href="/pricing"
            />
            <PriceCard
              name="Pro"
              price="$13"
              priceINR="₹999/mo"
              credits="500 min/month"
              features={[
                "5 hooks per video",
                "Unlimited Shorts",
                "Advanced analytics",
                "Priority support",
              ]}
              cta="Go Pro"
              href="/pricing"
            />
          </div>
          <p className="text-center mt-8">
            <Link href="/pricing" className="text-[#E84A2F] text-sm font-medium hover:underline">
              See full pricing →
            </Link>
          </p>
        </div>
      </section>

      {/* ── 10. FINAL CTA ── */}
      <section className="bg-[#111] border-t border-white/[0.05] py-24 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-[clamp(32px,5vw,68px)] font-extrabold text-white mb-3 tracking-[-0.04em] leading-[1.05] font-[family-name:--font-display]">
            Your next viral Short
            <br />
            is already in your video.
          </h2>
          <p className="text-white/30 text-base mb-10">Find it in under 2 minutes.</p>
          <Link
            href="/auth/login"
            className="inline-flex items-center gap-2.5 btn-primary px-9 py-4 rounded-full text-base font-semibold"
          >
            Start Analyzing Free
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <p className="text-white/20 text-xs mt-4">120 minutes free · No credit card required</p>
        </div>
      </section>
    </div>
  );
}

export default MarketingHome;
