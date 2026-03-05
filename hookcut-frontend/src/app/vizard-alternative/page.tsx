import type { Metadata } from "next";
import { AlternativePage, type CompetitorData } from "@/components/alternative-page";

export const metadata: Metadata = {
  title: "Best Vizard Alternative for Hook Scoring & Shorts | HookCut",
  description:
    "Want a Vizard alternative that scores hooks instead of just identifying timestamps? HookCut's 0–100 Hook Score tells you which moments are most likely to go viral — before you post.",
  openGraph: {
    title: "Best Vizard Alternative for Hook Scoring & Shorts | HookCut",
    description:
      "HookCut's 0–100 Hook Score tells you which moments are most likely to go viral — before you post.",
    type: "website",
    url: "https://hookcut.ai/vizard-alternative",
  },
  twitter: {
    card: "summary_large_image",
    title: "Best Vizard Alternative for Hook Scoring & Shorts | HookCut",
    description:
      "HookCut's 0–100 Hook Score tells you which moments are most likely to go viral — before you post.",
  },
  alternates: { canonical: "https://hookcut.ai/vizard-alternative" },
};

const data: CompetitorData = {
  competitor: "Vizard",
  competitorSlug: "vizard",
  headline: "The Best Vizard Alternative That Scores Every Hook Before You Clip It",
  intro:
    "Vizard does a solid job of identifying segments in long-form videos and trimming them into clips. What it doesn't do is tell you which segments are worth posting and why. HookCut fills that gap with a 0–100 Hook Score for every identified moment — powered by an analysis of hook type, engagement potential, and viewer psychology. If you've been using Vizard and still spending time manually reviewing clips to find the good ones, HookCut eliminates that step entirely.",
  tableRows: [
    {
      feature: "Hook scoring (0–100)",
      hookcut: "✓ Every hook scored",
      competitor: "✗ No scoring",
      hookcutWins: true,
    },
    {
      feature: "Explains why each clip works",
      hookcut: "✓ 3 insight rows per hook",
      competitor: "✗ No explanation",
      hookcutWins: true,
    },
    {
      feature: "Auto-rejects filler/intro clips",
      hookcut: "✓",
      competitor: "✗",
      hookcutWins: true,
    },
    {
      feature: "Hook type classification",
      hookcut: "✓ 18 hook types",
      competitor: "✗ None",
      hookcutWins: true,
    },
    {
      feature: "Price / month (USD)",
      hookcut: "From $9/mo",
      competitor: "From $20/mo",
      hookcutWins: true,
    },
    {
      feature: "India pricing (INR + UPI)",
      hookcut: "✓ ₹499/mo + UPI",
      competitor: "✗ USD only",
      hookcutWins: true,
    },
    {
      feature: "Regional language support",
      hookcut: "✓ 12+ languages",
      competitor: "Limited",
      hookcutWins: true,
    },
    {
      feature: "Cancel anytime",
      hookcut: "✓",
      competitor: "✓",
      hookcutWins: false,
    },
  ],
  reasons: [
    {
      title: "Know Which Clips to Post Before You Download Them",
      description:
        "Vizard shows you segments — you decide which to keep. HookCut scores every moment first. See which hook scored 87 vs. which scored 42, understand why, and only download the ones worth your time. Stop reviewing clips manually. Let the score guide you.",
    },
    {
      title: "Hook Types That Tell You What You're Working With",
      description:
        "HookCut classifies every hook into one of 18 types — Curiosity Gap, Shock Statistic, Contrarian Claim, Pain Escalation, Social Proof, and more. Knowing the hook type tells you how to structure your Short, what caption to write, and how to set viewer expectations. Vizard doesn't classify hook types at all.",
    },
    {
      title: "India-First Pricing and Languages",
      description:
        "HookCut is priced at ₹499/month with UPI support — built for creators across India. Vizard offers no regional pricing. HookCut also handles Hinglish, Hindi, Tamil, Telugu, and 12+ other Indian languages in its transcript analysis, so the hook scoring works accurately regardless of your content language.",
    },
  ],
  faqs: [
    {
      q: "How is HookCut different from Vizard?",
      a: "Vizard identifies segments in your video and lets you choose what to clip. HookCut scores every potential hook moment from 0–100 and explains why each one is or isn't worth posting. The key difference is intelligence: HookCut tells you which moments are most likely to go viral before you spend time editing them.",
    },
    {
      q: "Does HookCut work with YouTube like Vizard?",
      a: "Yes. Paste any public YouTube URL — no file upload needed. HookCut fetches the transcript and returns scored hook moments in under 2 minutes.",
    },
    {
      q: "Can I trim hooks before downloading?",
      a: "Yes. Every hook in HookCut includes a ±10 second trim control so you can adjust the start and end points before generating your Short.",
    },
    {
      q: "Does HookCut generate 9:16 vertical videos?",
      a: "Yes. Every generated Short is in 9:16 format with auto-captions — ready to post on YouTube Shorts, Instagram Reels, or TikTok.",
    },
    {
      q: "Is there a free plan?",
      a: "Every new HookCut account includes 120 free minutes of video analysis — no credit card required to get started.",
    },
  ],
};

export default function VizardAlternativePage() {
  return <AlternativePage data={data} />;
}
