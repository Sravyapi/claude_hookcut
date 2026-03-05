import type { Metadata } from "next";
import { AlternativePage, type CompetitorData } from "@/components/alternative-page";

export const metadata: Metadata = {
  title: "Best Submagic Alternative for Viral Hook Detection | HookCut",
  description:
    "Submagic adds captions. HookCut finds the hooks worth captioning. Get scored, explained hook moments from any YouTube video — then generate your Short with captions included.",
  openGraph: {
    title: "Best Submagic Alternative for Viral Hook Detection | HookCut",
    description:
      "HookCut finds the hooks worth captioning. Get scored hook moments from any YouTube video — then generate your Short with captions included.",
    type: "website",
    url: "https://hookcut.ai/submagic-alternative",
  },
  twitter: {
    card: "summary_large_image",
    title: "Best Submagic Alternative for Viral Hook Detection | HookCut",
    description:
      "HookCut finds the hooks worth captioning. Get scored hook moments from any YouTube video — then generate your Short with captions included.",
  },
  alternates: { canonical: "https://hookcut.ai/submagic-alternative" },
};

const data: CompetitorData = {
  competitor: "Submagic",
  competitorSlug: "submagic",
  headline: "The Best Submagic Alternative That Finds Hooks Before Adding Captions",
  intro:
    "Submagic is excellent at what it does — generating animated, stylized captions for videos. But captions are the finishing touch, not the starting point. HookCut solves the harder problem: identifying which moments in your YouTube video are worth captioning in the first place. Paste any YouTube URL, and HookCut analyzes the transcript, scores every hook moment from 0 to 100, and returns the top 5 with explanations. Then it generates your Short with captions included — in four preset styles. Hook discovery and caption generation, in one tool.",
  tableRows: [
    {
      feature: "Hook scoring (0–100)",
      hookcut: "✓ Every hook scored",
      competitor: "✗ No hook detection",
      hookcutWins: true,
    },
    {
      feature: "Hook discovery from YouTube URL",
      hookcut: "✓ Automatic",
      competitor: "✗ Manual clip required",
      hookcutWins: true,
    },
    {
      feature: "Explains why each hook works",
      hookcut: "✓ 3 insights per hook",
      competitor: "✗ Not applicable",
      hookcutWins: true,
    },
    {
      feature: "Auto-captions on generated Shorts",
      hookcut: "✓ 4 styles included",
      competitor: "✓ Core feature",
      hookcutWins: false,
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
      feature: "Multi-language transcript support",
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
      title: "Find the Hook First, Then Caption It",
      description:
        "Submagic's workflow starts with a clip you've already selected. HookCut's workflow starts with your raw YouTube video — analyze the full transcript, score every potential hook, surface the top 5, and then generate the Short with captions. It's the complete pipeline from URL to ready-to-post Short, not just the captioning step.",
    },
    {
      title: "Hooks That Are Scored, Not Guessed",
      description:
        "Every hook HookCut surfaces has a 0–100 score and three rows of explanation: the platform dynamic, the viewer psychology, and a creator tip. You're not guessing which clip might perform — you're looking at scored, explained moments ranked by engagement potential. Caption the right clips and they have a real shot at going viral.",
    },
    {
      title: "All-In Pricing for Indian Creators",
      description:
        "HookCut packages hook detection, Shorts generation, and auto-captions into one tool at ₹499/month — paid in rupees via UPI. Submagic's pricing starts higher in USD, and adding hook detection would require a separate tool. HookCut is the all-in-one solution priced for creators across India.",
    },
  ],
  faqs: [
    {
      q: "Can HookCut replace both Submagic and a clip finder?",
      a: "For most creators, yes. HookCut detects hook moments from YouTube URLs, scores them, and generates 9:16 Shorts with auto-captions in 4 styles. If you're using a separate tool to find clips and Submagic to add captions, HookCut can consolidate that into one workflow.",
    },
    {
      q: "What caption styles does HookCut offer?",
      a: "HookCut includes 4 caption presets: Clean (minimal, white text), Bold (high-contrast, black background), Neon (energetic, colorful), and Minimal (subtle, small caps). All styles are auto-generated and embedded in the Short.",
    },
    {
      q: "Does HookCut work with YouTube videos directly?",
      a: "Yes. Paste any public YouTube URL — no file upload needed. HookCut fetches and analyzes the transcript automatically, typically in under 2 minutes.",
    },
    {
      q: "Does HookCut support Hindi and regional Indian languages?",
      a: "Yes. HookCut supports 12+ Indian languages including Hindi, Tamil, Telugu, Kannada, and Hinglish. The hook scoring works across languages.",
    },
    {
      q: "Is there a free trial?",
      a: "Yes. Every new account includes 120 free minutes — no credit card required.",
    },
  ],
};

export default function SubmagicAlternativePage() {
  return <AlternativePage data={data} />;
}
