import type { Metadata } from "next";
import { AlternativePage, type CompetitorData } from "@/components/alternative-page";

export const metadata: Metadata = {
  title: "Best Choppity Alternative for Hook Analysis | HookCut",
  description:
    "Looking for a Choppity alternative with hook scoring? HookCut finds the 5 moments in any YouTube video most likely to go viral — scored 0–100 with explanations, not just timestamps.",
  openGraph: {
    title: "Best Choppity Alternative for Hook Analysis | HookCut",
    description:
      "HookCut finds the 5 moments in any YouTube video most likely to go viral — scored 0–100 with explanations, not just timestamps.",
    type: "website",
    url: "https://hookcut.ai/choppity-alternative",
  },
  twitter: {
    card: "summary_large_image",
    title: "Best Choppity Alternative for Hook Analysis | HookCut",
    description:
      "HookCut finds the 5 moments in any YouTube video most likely to go viral — scored 0–100 with explanations.",
  },
  alternates: { canonical: "https://hookcut.ai/choppity-alternative" },
};

const data: CompetitorData = {
  competitor: "Choppity",
  competitorSlug: "choppity",
  headline: "The Best Choppity Alternative That Scores Hooks Instead of Just Chopping Video",
  intro:
    "Choppity earned its name — it chops your video into short clips quickly. But quick clips and viral clips are not the same thing. HookCut analyzes the full transcript of your YouTube video, identifies every potential hook moment, and scores each one from 0 to 100 based on engagement potential. You get 5 scored, explained hooks — not a pile of clips to manually sort through. If you're ready for a Choppity alternative that prioritizes quality over speed, HookCut is built for you.",
  tableRows: [
    {
      feature: "Hook scoring (0–100)",
      hookcut: "✓ Every hook scored",
      competitor: "✗ No scoring",
      hookcutWins: true,
    },
    {
      feature: "Explains why each clip was chosen",
      hookcut: "✓ 3 insight rows",
      competitor: "✗ No explanation",
      hookcutWins: true,
    },
    {
      feature: "Filters out filler/greeting clips",
      hookcut: "✓ Auto-filtered",
      competitor: "✗ Manual review required",
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
      competitor: "From $15/mo",
      hookcutWins: true,
    },
    {
      feature: "India pricing (INR + UPI)",
      hookcut: "✓ ₹499/mo + UPI",
      competitor: "✗ USD only",
      hookcutWins: true,
    },
    {
      feature: "Multi-language support",
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
      title: "A Score, Not Just a Timestamp",
      description:
        "Choppity identifies moments worth clipping. HookCut scores them. A 0–100 Hook Score lets you instantly see which moments have the highest engagement potential and which ones to skip — without watching a single second of footage. The score replaces the manual review step that every Choppity user knows too well.",
    },
    {
      title: "Learn Why a Hook Works",
      description:
        "Alongside every scored hook, HookCut provides three rows of insight: the platform dynamic at play, the viewer psychology being triggered, and a creator tip to maximize impact. You don't just get a clip — you get a brief on why it's likely to perform. Over time, this changes how you structure your content from the start.",
    },
    {
      title: "No Dollar Pricing for Indian Creators",
      description:
        "HookCut charges ₹499/month in Indian rupees with UPI support. No dollar conversion, no international card fees. Choppity has no regional pricing for India. If you're creating for an Indian audience in Hindi, Hinglish, or any regional language, HookCut is built for your workflow — not retrofitted to it.",
    },
  ],
  faqs: [
    {
      q: "How is HookCut different from Choppity?",
      a: "Choppity chops your video into clips quickly — good for volume. HookCut takes a quality-first approach: score every potential hook moment, surface only the top 5, and explain exactly why each one is worth posting. Less output, more signal.",
    },
    {
      q: "Does HookCut require video upload like Choppity?",
      a: "No. HookCut works from a YouTube URL — paste the link, and HookCut fetches and analyzes the transcript automatically. No file upload needed.",
    },
    {
      q: "Can I trim clips in HookCut?",
      a: "Yes. Each hook includes ±10 second trim controls so you can fine-tune the start and end points before generating your Short.",
    },
    {
      q: "Does HookCut include captions?",
      a: "Yes. Every generated 9:16 Short includes auto-captions in one of 4 preset styles: Clean, Bold, Neon, or Minimal.",
    },
    {
      q: "Is there a free trial for HookCut?",
      a: "Yes. Every new account starts with 120 free minutes of analysis — no credit card required.",
    },
  ],
};

export default function ChoppityAlternativePage() {
  return <AlternativePage data={data} />;
}
