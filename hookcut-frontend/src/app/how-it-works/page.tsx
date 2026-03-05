import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "How It Works | HookCut — Hook Analysis in 3 Steps",
  description:
    "Paste a YouTube URL. HookCut analyzes the transcript, scores the top hook moments, and generates vertical Shorts — in under 2 minutes.",
  openGraph: {
    title: "How It Works | HookCut",
    description: "Paste a YouTube URL. Get scored hooks and ready-to-post Shorts in under 2 minutes.",
    type: "website",
    url: "https://hookcut.ai/how-it-works",
  },
  twitter: { card: "summary_large_image", title: "How It Works | HookCut", description: "Paste a YouTube URL. Get scored hooks and ready-to-post Shorts in under 2 minutes." },
  alternates: { canonical: "https://hookcut.ai/how-it-works" },
};

const STEPS = [
  {
    number: "01",
    title: "Paste your YouTube URL",
    description:
      "Any YouTube video works — long-form uploads, podcasts, webinars, vlogs, educational content. Public videos only. Choose your content niche and language to improve analysis accuracy.",
    detail:
      "Works on videos of any length. There's no file upload — HookCut fetches the transcript directly from YouTube. Results arrive faster on shorter videos, but analysis works on 3-hour episodes just as well.",
    badge: "~10 seconds",
    badgeLabel: "to submit",
  },
  {
    number: "02",
    title: "HookCut analyzes the transcript",
    description:
      "Once submitted, HookCut fetches the full video transcript and runs it through the hook analysis engine. The process has three stages: transcript extraction → hook detection → engagement ranking.",
    detail:
      "The engine looks for moments of tension, curiosity, and emotion — the psychological triggers that cause viewers to stop scrolling. Every detected moment gets classified by hook type and scored 0–10.",
    badge: "~90 seconds",
    badgeLabel: "for analysis",
  },
  {
    number: "03",
    title: "Review your scored hooks",
    description:
      "You get up to 5 hook moments, each with a score, hook type classification, timestamp, and insight panel. The score reflects engagement potential — not views, not guesses.",
    detail:
      "Each hook card shows: Score gauge · Hook type · Funnel role · Hook text · Platform Dynamics insight · Viewer Psychology note · Creator Tip. Select up to 3 hooks to generate Shorts from. You can fine-tune clip boundaries ±10 seconds before generating.",
    badge: "You decide",
    badgeLabel: "which hooks to clip",
  },
  {
    number: "04",
    title: "Choose a caption style",
    description:
      "Before generating, choose how your captions will look. Four presets: Clean (professional), Bold (high-energy), Neon (trendy), and Minimal (subtle). Captions are burnt directly into the video.",
    detail:
      "Caption style affects the font weight, color, and background of the on-screen text. All styles are designed for 9:16 vertical video and are readable on mobile without tapping.",
    badge: "4 styles",
    badgeLabel: "to choose from",
  },
  {
    number: "05",
    title: "Generate and download your Shorts",
    description:
      "Click Generate. HookCut processes each selected hook into a 9:16 vertical video with burnt-in captions. Download links appear within 2 minutes — valid for 24 hours.",
    detail:
      "Videos are rendered at 1080×1920 (standard Shorts/Reels resolution). Credits are deducted per minute of source video analyzed — not per clip generated. If processing fails, your credits are automatically returned.",
    badge: "~2 minutes",
    badgeLabel: "to download",
  },
  {
    number: "06",
    title: "Post. Repeat.",
    description:
      "Your Shorts are ready for YouTube Shorts, Instagram Reels, TikTok, or any vertical video platform. No watermark. No HookCut branding. Yours to use however you want.",
    detail:
      "Most creators run HookCut on one video per week. At ₹499/month, that's roughly ₹125 per video — less than the cost of one freelance clip. The hook scores give you data on which moments work, so your content improves over time.",
    badge: "Post anywhere",
    badgeLabel: "no watermarks",
  },
];

const FAQS = [
  {
    q: "What kinds of videos does HookCut work on?",
    a: "Any public YouTube video with auto-generated or manual captions. This includes talking-head videos, podcasts uploaded to YouTube, webinars, educational content, vlogs, and interviews. Videos without any transcript data cannot be analyzed.",
  },
  {
    q: "How long does analysis take?",
    a: "Most videos under 30 minutes analyze in under 90 seconds. Longer videos (60–120 min) take 2–4 minutes. You can leave the tab open and come back — the result is saved to your session.",
  },
  {
    q: "Can I adjust the clip boundaries?",
    a: "Yes. After selecting hooks, you get trim sliders for each selected clip. You can expand or contract the start and end points up to 10 seconds in either direction before generating.",
  },
  {
    q: "What if the analysis doesn't find good hooks?",
    a: "You can regenerate hooks with a single click. The first regeneration is free. Subsequent regenerations deduct a small credit fee. If you're consistently getting poor results, the video may not have strong hook moments — which is itself useful information.",
  },
  {
    q: "What languages are supported?",
    a: "English (primary), Hindi, Hinglish, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, and Urdu. More languages coming based on demand.",
  },
];

export default function HowItWorksPage() {
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQS.map((faq) => ({
      "@type": "Question",
      name: faq.q,
      acceptedAnswer: { "@type": "Answer", text: faq.a },
    })),
  };

  return (
    <div className="bg-[#FAFAF8] min-h-screen">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#E84A2F] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      {/* Hero */}
      <section className="pt-32 pb-16 px-6 text-center">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-5xl sm:text-6xl font-[family-name:--font-display] font-bold text-[#0A0A0A] leading-tight tracking-tight mb-6">
            From YouTube URL<br />to viral Short in 6 steps.
          </h1>
          <p className="text-lg text-[#71717A] leading-relaxed mb-8 max-w-2xl mx-auto">
            HookCut analyzes your video&apos;s transcript, identifies the top hook moments, scores each one,
            and generates ready-to-post vertical Shorts — all in under 2 minutes.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
          >
            Try it now — 120 minutes free
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </section>

      <main id="main-content">
        {/* Step list */}
        <section className="py-16 px-6">
          <div className="max-w-3xl mx-auto space-y-0">
            {STEPS.map((step, i) => (
              <div key={step.number} className="relative flex gap-8">
                {/* Connector line */}
                <div className="flex flex-col items-center shrink-0">
                  <div className="w-10 h-10 rounded-full bg-[#E84A2F] text-white flex items-center justify-center text-sm font-bold shrink-0">
                    {i + 1}
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className="w-px flex-1 bg-[#E4E4E7] mt-3 mb-3 min-h-[3rem]" aria-hidden="true" />
                  )}
                </div>

                {/* Content */}
                <div className="pb-10">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-xl font-[family-name:--font-display] font-bold text-[#0A0A0A]">
                      {step.title}
                    </h2>
                    <span className="px-2.5 py-0.5 rounded-full bg-[#E84A2F]/10 text-[#E84A2F] text-xs font-semibold">
                      {step.badge}
                    </span>
                  </div>
                  <p className="text-[#0A0A0A] font-medium mb-2 leading-relaxed">{step.description}</p>
                  <p className="text-[#71717A] text-sm leading-relaxed">{step.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* FAQ */}
        <section className="py-16 px-6 bg-white border-t border-[#E4E4E7]">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-10">
              Frequently asked questions
            </h2>
            <dl className="space-y-6">
              {FAQS.map((faq) => (
                <div key={faq.q} className="border-b border-[#E4E4E7] pb-6 last:border-0 last:pb-0">
                  <dt className="font-semibold text-[#0A0A0A] mb-2">{faq.q}</dt>
                  <dd className="text-[#71717A] leading-relaxed text-sm">{faq.a}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-24 px-6 bg-[#0A0A0A] text-center">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-4xl font-[family-name:--font-display] font-bold text-white mb-4">
              Ready to find your hooks?
            </h2>
            <p className="text-white/50 mb-10">Paste any YouTube URL. First 120 minutes are free.</p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-[#E84A2F] text-white font-semibold hover:bg-[#D13F25] transition-colors"
            >
              Start Analyzing
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}
