import type { Metadata } from "next";
import { AlternativePage, type CompetitorData } from "@/components/alternative-page";

export const metadata: Metadata = {
  title: "Best AI Hook Finder for YouTube Videos | HookCut",
  description:
    "HookCut is the best AI hook finder for YouTube creators. Paste any URL, get the top 5 hook moments scored 0–100 with explanations — and download them as Shorts in under 2 minutes.",
  openGraph: {
    title: "Best AI Hook Finder for YouTube Videos | HookCut",
    description:
      "HookCut is the best AI hook finder for YouTube creators. Get scored hook moments with explanations — ready as Shorts in under 2 minutes.",
    type: "website",
    url: "https://hookcut.ai/ai-hook-finder",
  },
  twitter: {
    card: "summary_large_image",
    title: "Best AI Hook Finder for YouTube Videos | HookCut",
    description:
      "HookCut is the best AI hook finder for YouTube creators. Get scored hook moments with explanations — ready as Shorts in under 2 minutes.",
  },
  alternates: { canonical: "https://hookcut.ai/ai-hook-finder" },
};

const data: CompetitorData = {
  competitor: "Generic AI Clippers",
  competitorSlug: "generic-clippers",
  headline: "The Best AI Hook Finder for YouTube Creators",
  intro:
    "Most AI video tools generate clips. HookCut is built specifically to find hooks — the moments in your YouTube video that are most likely to stop someone from scrolling. Paste any public YouTube URL, and HookCut's AI analyzes the full transcript to surface the top 5 hook moments, each scored from 0 to 100. You get the exact timestamps, the hook type (Curiosity Gap, Shock Statistic, Contrarian Claim, and 15 others), and a plain-English explanation of why each moment is likely to perform. Then generate your Short with one click.",
  tableRows: [
    {
      feature: "Hook-specific analysis (not just clipping)",
      hookcut: "✓ Built for hooks",
      competitor: "✗ Generic clips",
      hookcutWins: true,
    },
    {
      feature: "0–100 Hook Score per moment",
      hookcut: "✓ Every hook scored",
      competitor: "✗ No scoring",
      hookcutWins: true,
    },
    {
      feature: "18 hook type classifications",
      hookcut: "✓",
      competitor: "✗",
      hookcutWins: true,
    },
    {
      feature: "Platform + psychology insights",
      hookcut: "✓ 3 rows per hook",
      competitor: "✗",
      hookcutWins: true,
    },
    {
      feature: "Auto-rejects filler/intro segments",
      hookcut: "✓",
      competitor: "✗",
      hookcutWins: true,
    },
    {
      feature: "Price / month (USD)",
      hookcut: "From $9/mo",
      competitor: "Varies ($15–$30+)",
      hookcutWins: true,
    },
    {
      feature: "India pricing (INR + UPI)",
      hookcut: "✓ ₹499/mo + UPI",
      competitor: "✗",
      hookcutWins: true,
    },
    {
      feature: "Cancel anytime",
      hookcut: "✓",
      competitor: "Varies",
      hookcutWins: false,
    },
  ],
  reasons: [
    {
      title: "Built Specifically to Find Hooks",
      description:
        "Generic AI clippers look for scene changes, energy spikes, and filler removal. HookCut's analysis is purpose-built for a single outcome: identifying the moments in your video that are most likely to stop a scroll. Every identified moment is scored, classified by hook type, and explained in plain English. This is hook-finding — not just clipping.",
    },
    {
      title: "18 Hook Types, Not Just 'Highlights'",
      description:
        "HookCut classifies every identified moment into one of 18 hook categories: Curiosity Gap, Shock Statistic, Pain Escalation, Contrarian Claim, Social Proof, Open Loop, and more. Knowing the hook type tells you how to frame the Short, what to write in the caption, and what viewer emotion you're targeting. Generic AI clippers give you clips; HookCut gives you strategy.",
    },
    {
      title: "The Only AI Hook Finder Built for Indian Creators",
      description:
        "HookCut supports Hinglish and 12+ Indian regional languages — not as a beta feature, but as a core part of the analysis engine. Pay in INR via UPI at ₹499/month. No dollar pricing, no international card fees. Whether you're creating in Hindi, Tamil, Telugu, or switching between languages mid-sentence, HookCut finds the hooks.",
    },
  ],
  faqs: [
    {
      q: "What makes HookCut the best AI hook finder?",
      a: "HookCut is purpose-built for hook identification — not repurposed from a general clipping tool. It analyzes the full transcript of your YouTube video, classifies every potential hook moment into 18 types, scores each from 0 to 100, and explains the platform dynamic, viewer psychology, and creator tip behind each one. No other AI hook finder provides this level of detail.",
    },
    {
      q: "How does AI hook finding work in HookCut?",
      a: "Paste a YouTube URL. HookCut fetches the transcript, runs it through a multi-stage analysis to identify hook moments by type and score them by engagement potential, then returns the top 5 ranked results. The process typically takes under 2 minutes for videos up to 90 minutes long.",
    },
    {
      q: "What hook types does HookCut detect?",
      a: "HookCut classifies hooks across 18 types including Curiosity Gap, Shock Statistic, Contrarian Claim, Pain Escalation, Social Proof, Open Loop, Transformation Reveal, Confession, and more. Each hook's type appears alongside its score in the results.",
    },
    {
      q: "Does the AI hook finder work for long videos?",
      a: "Yes. HookCut analyzes videos up to 90+ minutes. The longer the video, the more potential hook moments — and the more valuable the scoring is, since it helps you quickly identify the top 5 without rewatching hours of footage.",
    },
    {
      q: "How much does the AI hook finder cost?",
      a: "HookCut starts at $9/month (or ₹499/month for Indian creators). Every new account includes 120 free minutes — no credit card required to start.",
    },
  ],
};

export default function AiHookFinderPage() {
  return <AlternativePage data={data} />;
}
