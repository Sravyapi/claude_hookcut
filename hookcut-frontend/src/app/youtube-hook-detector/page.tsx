import type { Metadata } from "next";
import { AlternativePage, type CompetitorData } from "@/components/alternative-page";

export const metadata: Metadata = {
  title: "YouTube Hook Detector — Find Viral Moments in Any Video | HookCut",
  description:
    "HookCut is the #1 YouTube hook detector. Paste any video URL and detect the top 5 hook moments — each scored 0–100 and explained. Download as a 9:16 Short in under 2 minutes.",
  openGraph: {
    title: "YouTube Hook Detector — Find Viral Moments in Any Video | HookCut",
    description:
      "HookCut detects the top 5 hook moments in any YouTube video — scored 0–100 with explanations. Download as Shorts in under 2 minutes.",
    type: "website",
    url: "https://hookcut.ai/youtube-hook-detector",
  },
  twitter: {
    card: "summary_large_image",
    title: "YouTube Hook Detector — Find Viral Moments in Any Video | HookCut",
    description:
      "HookCut detects the top 5 hook moments in any YouTube video — scored 0–100 with explanations. Download as Shorts in under 2 minutes.",
  },
  alternates: { canonical: "https://hookcut.ai/youtube-hook-detector" },
};

const data: CompetitorData = {
  competitor: "Manual Review",
  competitorSlug: "manual-review",
  headline: "The Fastest YouTube Hook Detector for Creators",
  intro:
    "Detecting hooks manually means watching your entire video, rewinding at interesting moments, noting timestamps, and repeating until you've found the most scroll-stopping segment. It takes hours. HookCut is a YouTube hook detector that does it in under 2 minutes — analyzing the full transcript, identifying every potential hook moment, classifying it by type, and scoring it from 0 to 100. Paste your YouTube URL. Get your top 5 hooks. Download your Shorts. No manual review required.",
  tableRows: [
    {
      feature: "Automatic hook detection",
      hookcut: "✓ Full transcript analysis",
      competitor: "✗ Manual review",
      hookcutWins: true,
    },
    {
      feature: "Hook scoring (0–100)",
      hookcut: "✓ Every hook scored",
      competitor: "✗ No scoring",
      hookcutWins: true,
    },
    {
      feature: "Hook type classification",
      hookcut: "✓ 18 hook types",
      competitor: "✗ Not classified",
      hookcutWins: true,
    },
    {
      feature: "Insight explanation per hook",
      hookcut: "✓ 3 rows per hook",
      competitor: "✗ None",
      hookcutWins: true,
    },
    {
      feature: "Time to detect hooks",
      hookcut: "~2 minutes",
      competitor: "Hours",
      hookcutWins: true,
    },
    {
      feature: "Short generation included",
      hookcut: "✓ 9:16 + captions",
      competitor: "✗ Separate editing required",
      hookcutWins: true,
    },
    {
      feature: "India pricing (INR + UPI)",
      hookcut: "✓ ₹499/mo + UPI",
      competitor: "N/A",
      hookcutWins: true,
    },
    {
      feature: "Free to start",
      hookcut: "✓ 120 free minutes",
      competitor: "Free (but your time)",
      hookcutWins: true,
    },
  ],
  reasons: [
    {
      title: "Detect Hooks in 2 Minutes, Not 2 Hours",
      description:
        "The old way of finding hooks: watch your entire video, identify interesting moments, rewind and note timestamps, compare and select the best one. With a 45-minute video, that process takes hours. HookCut's hook detector analyzes the full transcript in under 2 minutes and returns ranked results. The same video that used to take two hours now takes two minutes.",
    },
    {
      title: "Not Just Detection — Classification and Scoring",
      description:
        "Knowing a moment is interesting isn't enough. HookCut's YouTube hook detector classifies every identified moment into one of 18 hook types (Curiosity Gap, Shock Statistic, Contrarian Claim, Open Loop, etc.) and scores each one from 0 to 100. You see which type of hook you're working with, how strong it is, and a plain-English explanation of why it's likely to perform.",
    },
    {
      title: "Detection to Download in One Workflow",
      description:
        "Most YouTube hook detectors stop at detection — you still need separate editing software to generate the Short. HookCut goes from detection to download in the same workflow. Select up to 3 hooks, choose a caption style, and generate your 9:16 Shorts with captions embedded. Paste URL → detect hooks → download Shorts.",
    },
  ],
  faqs: [
    {
      q: "How does HookCut detect YouTube hooks?",
      a: "HookCut fetches the transcript from any public YouTube video and runs a multi-stage analysis to identify moments with high scroll-stopping potential. Each moment is classified by hook type (18 types available), scored from 0 to 100, and explained with platform dynamics, viewer psychology, and creator tips. The top 5 are returned, ranked by score.",
    },
    {
      q: "What kinds of hooks can the YouTube hook detector find?",
      a: "HookCut detects 18 hook types including: Curiosity Gap (creates information gaps), Shock Statistic (surprising data), Contrarian Claim (challenges common belief), Pain Escalation (amplifies a viewer problem), Open Loop (delays resolution), Social Proof (leverages authority), Transformation Reveal, Confession, and more.",
    },
    {
      q: "Does the hook detector work on long YouTube videos?",
      a: "Yes. HookCut works on YouTube videos of any length. For longer videos (60–90+ minutes), hook detection typically takes 2–4 minutes. The longer the video, the more valuable the scoring becomes — it filters the best moments so you don't have to.",
    },
    {
      q: "Can I detect hooks in Hindi or regional Indian language videos?",
      a: "Yes. HookCut's hook detector supports 12+ Indian languages including Hindi, Tamil, Telugu, Kannada, Malayalam, and Hinglish. The scoring and classification works accurately across languages.",
    },
    {
      q: "Is the YouTube hook detector free to try?",
      a: "Yes. Every new HookCut account includes 120 free minutes of video analysis — no credit card required. That's enough to analyze several full-length YouTube videos.",
    },
  ],
};

export default function YouTubeHookDetectorPage() {
  return <AlternativePage data={data} />;
}
