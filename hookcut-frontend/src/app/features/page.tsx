import type { Metadata } from "next";
import Link from "next/link";
import Header from "@/components/header";

export const metadata: Metadata = {
  title: "Features | HookCut — Hook Analysis Engine for YouTube Shorts",
  description:
    "HookCut identifies the scroll-stopping moments in any YouTube video. Scored, explained, clipped, and ready to post as Shorts in under 2 minutes.",
  openGraph: {
    title: "Features | HookCut",
    description: "Hook scoring, 18 hook types, composite detection, penalty filtering, and transparent credit billing.",
    type: "website",
    url: "https://hookcut.ai/features",
  },
  twitter: { card: "summary_large_image", title: "Features | HookCut", description: "Hook scoring, 18 hook types, composite detection, penalty filtering, and transparent credit billing." },
  alternates: { canonical: "https://hookcut.ai/features" },
};

const FEATURES = [
  {
    id: "hook-score",
    number: "01",
    title: "Hook Score Engine",
    tagline: "Every moment gets a score. Only the best ones ship.",
    description:
      "HookCut analyzes every moment in your video and assigns a score reflecting its scroll-stopping potential. Higher scores mean higher engagement probability. Each hook card shows the score front and center — no guessing required.",
    details: [
      "Score from 0–10 for each detected hook moment",
      "Color-coded by engagement tier (red → amber → orange → green)",
      "Grade label included: Needs Work · Moderate · High Impact · Exceptional",
    ],
    visual: (
      <div className="bg-[#111111] rounded-2xl p-6 text-center">
        <div className="relative w-24 h-24 mx-auto mb-3">
          <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
            <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" />
            <circle cx="40" cy="40" r="36" fill="none" stroke="#16A34A" strokeWidth="5" strokeLinecap="round"
              strokeDasharray="226" strokeDashoffset="22" />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-white font-mono">9.0</span>
            <span className="text-[9px] text-white/30 uppercase tracking-wider">score</span>
          </div>
        </div>
        <span className="text-sm font-semibold text-[#16A34A]">Exceptional</span>
      </div>
    ),
  },
  {
    id: "hook-types",
    number: "02",
    title: "18 Hook Type Classifications",
    tagline: "Know what kind of hook you're posting — before you post it.",
    description:
      "Not all hooks work the same way. HookCut classifies every identified moment into one of 18 hook categories — from curiosity gaps to pain escalation to social proof. This tells you exactly why a moment is likely to stop the scroll, so you can write better hooks in future videos.",
    details: [
      "18 distinct hook types: Curiosity Gap, Shock Statistic, Contrarian Claim, Pain Escalation, Open Loop, Social Proof, and 12 more",
      "Each hook type badge appears on the hook card",
      "Funnel role classification: TOFU · MOFU · BOFU",
    ],
    visual: (
      <div className="bg-[#111111] rounded-2xl p-5 space-y-2">
        {["CURIOSITY GAP", "SHOCK STATISTIC", "CONTRARIAN CLAIM", "PAIN ESCALATION", "OPEN LOOP"].map((type, i) => (
          <div key={type} className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${i === 0 ? "bg-[#E84A2F]" : i === 1 ? "bg-amber-400" : i === 2 ? "bg-blue-400" : i === 3 ? "bg-purple-400" : "bg-emerald-400"}`} />
            <span className="text-[11px] font-semibold tracking-wide text-white/70">{type}</span>
          </div>
        ))}
        <p className="text-[10px] text-white/30 pt-1">+13 more hook types</p>
      </div>
    ),
  },
  {
    id: "composite",
    number: "03",
    title: "Composite Hook Detection",
    tagline: "Some moments do more than one thing at once. We find those too.",
    description:
      "The most viral hooks often layer multiple psychological triggers — a shocking statistic that also opens a curiosity loop, or a contrarian claim backed by immediate proof. HookCut detects these composite moments and flags them so you know you're looking at a multi-layer hook.",
    details: [
      "Composite badge appears on hook cards with layered triggers",
      "Composite hooks consistently score higher than single-trigger moments",
      "Narrative arc classification: Intrigue → Proof → Escalation → Open Loop",
    ],
    visual: (
      <div className="bg-[#111111] rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[11px] px-2.5 py-0.5 rounded-full border font-semibold tracking-wide bg-amber-500/10 text-amber-300 border-amber-500/20">CURIOSITY GAP</span>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400/80 border border-amber-500/15">Composite</span>
        </div>
        <p className="text-[13px] text-white/70 leading-relaxed">
          "The one investment mistake that&apos;s quietly costing you thousands — and nobody&apos;s talking about it."
        </p>
      </div>
    ),
  },
  {
    id: "penalty",
    number: "04",
    title: "Intelligent Quality Filtering",
    tagline: "HookCut doesn't just find hooks — it discards the moments that won't work.",
    description:
      "Most AI clippers give you clips. HookCut gives you fewer, better clips by intelligently filtering out the moments that consistently underperform: greetings, sponsor reads, mid-sentence fragments, and filler transitions. The result is a Shorts library with no deadweight.",
    details: [
      "Greeting and intro segments automatically excluded",
      "Sponsor and ad-read segments filtered before scoring",
      "Mid-sentence cuts and filler transitions rejected",
    ],
    visual: (
      <div className="bg-[#111111] rounded-2xl p-5 space-y-2">
        {[
          { label: "\"Hey guys, welcome back...\"", pass: false },
          { label: "Sponsor segment (2:14–3:02)", pass: false },
          { label: "\"This shocked me — here's why.\"", pass: true },
          { label: "Mid-sentence fragment cut", pass: false },
          { label: "\"Nobody talks about this trick...\"", pass: true },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-2.5">
            <span className={`text-base ${item.pass ? "text-[#16A34A]" : "text-[#DC2626]"}`} aria-hidden="true">
              {item.pass ? "✓" : "✕"}
            </span>
            <span className={`text-[11px] ${item.pass ? "text-white/70" : "text-white/30 line-through"}`}>{item.label}</span>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: "billing",
    number: "05",
    title: "Transparent Credit Billing",
    tagline: "Pay for what you analyze. Credits refunded if processing fails.",
    description:
      "HookCut charges per minute of video analyzed — not per video, not per clip. A 10-minute video costs 10 credits. A 60-minute podcast costs 60. If analysis fails due to a processing error, your credits are automatically refunded. No billing surprises.",
    details: [
      "1 credit = 1 minute of video analyzed",
      "Failed analyses: credits automatically returned",
      "India pricing: ₹499/month — pay via UPI",
    ],
    visual: (
      <div className="bg-[#111111] rounded-2xl p-5">
        <div className="space-y-3">
          {[
            { label: "10-min YouTube video", credits: "10 credits", cost: "₹4.99" },
            { label: "60-min podcast episode", credits: "60 credits", cost: "₹29.93" },
            { label: "Failed analysis", credits: "Refunded", cost: "₹0" },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between border-b border-white/[0.05] pb-2 last:border-0 last:pb-0">
              <span className="text-[11px] text-white/50">{item.label}</span>
              <div className="flex items-center gap-3">
                <span className="text-[11px] font-mono text-[#E84A2F]">{item.credits}</span>
                <span className="text-[11px] font-mono text-white/30">{item.cost}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    ),
  },
];

export default function FeaturesPage() {
  return (
    <div className="bg-[#FAFAF8] min-h-screen">
      <Header />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#E84A2F] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#E84A2F]/10 border border-[#E84A2F]/20 text-[#E84A2F] text-xs font-semibold mb-6">
            What HookCut does
          </div>
          <h1 className="text-5xl sm:text-6xl font-[family-name:--font-display] font-bold text-[#0A0A0A] leading-tight tracking-tight mb-6">
            Built for hooks,<br />not clips.
          </h1>
          <p className="text-lg text-[#71717A] leading-relaxed max-w-2xl mx-auto mb-10">
            HookCut is a hook analysis engine. It doesn&apos;t just cut your video into clips — it identifies the moments
            most likely to stop a scroll, scores them, and explains why.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
          >
            Find My Hooks
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </section>

      <main id="main-content">
        {/* Feature sections */}
        <div className="divide-y divide-[#E4E4E7]">
          {FEATURES.map((feature, i) => (
            <section
              key={feature.id}
              id={feature.id}
              className={`py-20 px-6 ${i % 2 === 1 ? "bg-white" : "bg-[#FAFAF8]"}`}
            >
              <div className="max-w-5xl mx-auto">
                <div className={`grid grid-cols-1 lg:grid-cols-2 gap-12 items-center ${i % 2 === 1 ? "lg:grid-flow-dense" : ""}`}>
                  {/* Text side */}
                  <div className={i % 2 === 1 ? "lg:col-start-1" : ""}>
                    <div className="text-[#E84A2F] font-mono text-sm font-bold mb-3">{feature.number}</div>
                    <h2 className="text-3xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-3 leading-tight">
                      {feature.title}
                    </h2>
                    <p className="text-[#71717A] font-medium mb-4 text-sm">{feature.tagline}</p>
                    <p className="text-[#71717A] leading-relaxed mb-6">{feature.description}</p>
                    <ul className="space-y-2.5" aria-label={`${feature.title} details`}>
                      {feature.details.map((detail) => (
                        <li key={detail} className="flex items-start gap-2.5 text-sm text-[#71717A]">
                          <svg className="w-4 h-4 text-[#E84A2F] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                          </svg>
                          {detail}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Visual side */}
                  <div className={i % 2 === 1 ? "lg:col-start-2" : ""}>
                    {feature.visual}
                  </div>
                </div>
              </div>
            </section>
          ))}
        </div>

        {/* Final CTA */}
        <section className="py-24 px-6 bg-[#0A0A0A] text-center">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-4xl font-[family-name:--font-display] font-bold text-white mb-4">
              Your next viral Short is already in your video.
            </h2>
            <p className="text-white/50 mb-10">Find it in under 2 minutes.</p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-[#E84A2F] text-white font-semibold hover:bg-[#D13F25] transition-colors"
            >
              Start Analyzing
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
            <p className="text-white/25 text-xs mt-4">120 free minutes · No credit card · Results in ~2 minutes</p>
          </div>
        </section>
      </main>
    </div>
  );
}
