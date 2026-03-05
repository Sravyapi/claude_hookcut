import type { Metadata } from "next";
import { AlternativePage, type CompetitorData } from "@/components/alternative-page";

export const metadata: Metadata = {
  title: "YouTube Shorts Generator — Hook-Scored, Caption-Ready | HookCut",
  description:
    "HookCut is a YouTube Shorts generator that scores every clip before you download it. Get the top 5 hook moments from any YouTube video — scored, explained, and generated as 9:16 Shorts with captions.",
  openGraph: {
    title: "YouTube Shorts Generator — Hook-Scored, Caption-Ready | HookCut",
    description:
      "HookCut generates YouTube Shorts from the hook moments most likely to go viral — not just any moments. Scored, explained, captioned.",
    type: "website",
    url: "https://hookcut.ai/youtube-shorts-generator",
  },
  twitter: {
    card: "summary_large_image",
    title: "YouTube Shorts Generator — Hook-Scored, Caption-Ready | HookCut",
    description:
      "HookCut generates YouTube Shorts from the hook moments most likely to go viral — scored, explained, captioned.",
  },
  alternates: { canonical: "https://hookcut.ai/youtube-shorts-generator" },
};

const data: CompetitorData = {
  competitor: "Generic Shorts Generators",
  competitorSlug: "shorts-generators",
  headline: "The YouTube Shorts Generator That Scores Clips Before You Download Them",
  intro:
    "Most YouTube Shorts generators give you the same promise: paste a URL, get clips. The problem is that most clips they generate aren't hooks — they're random segments, mid-sentence cuts, or intro greetings that immediately lose viewers. HookCut generates YouTube Shorts differently: first, it analyzes the full transcript and scores every potential hook moment from 0 to 100. Then it generates only the top 5 — the moments most likely to stop a scroll. Every Short includes auto-captions in your choice of 4 styles. From URL to viral Short in under 2 minutes.",
  tableRows: [
    {
      feature: "Hook-scored before generation",
      hookcut: "✓ Scored 0–100 first",
      competitor: "✗ Random segments",
      hookcutWins: true,
    },
    {
      feature: "Explains why each Short will perform",
      hookcut: "✓ 3 insights per hook",
      competitor: "✗ No explanation",
      hookcutWins: true,
    },
    {
      feature: "18 hook type classifications",
      hookcut: "✓",
      competitor: "✗",
      hookcutWins: true,
    },
    {
      feature: "Auto-rejects filler/intro content",
      hookcut: "✓",
      competitor: "✗",
      hookcutWins: true,
    },
    {
      feature: "Auto-captions (4 styles)",
      hookcut: "✓ Clean, Bold, Neon, Minimal",
      competitor: "Varies",
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
      title: "Score First, Generate Second",
      description:
        "Generic Shorts generators take a shortcut: detect any plausible segment, generate the clip, let the creator sort it out. HookCut reverses the order. Every potential hook moment is scored from 0 to 100 before a single frame is rendered. You see the scores, read the explanations, and choose which ones to generate. No wasted render time on clips you'd never post.",
    },
    {
      title: "Shorts Built on Real Hooks",
      description:
        "A Short that starts with 'Hey guys, welcome back to my channel' isn't a hook — it's a scroll trigger. HookCut's analysis engine is trained to identify moments that trigger psychological responses: curiosity, tension, surprise, social proof. The result is Shorts that open with momentum instead of pleasantries. Classify your hooks first. Then generate.",
    },
    {
      title: "One Price. Hook Detection + Shorts Generation + Captions.",
      description:
        "Many creators use three separate tools: one to find clips, one to generate Shorts, one to add captions. HookCut combines all three. Analyze a YouTube URL, score your hooks, select up to 3, choose a caption style, and download your 9:16 Shorts — all in the same workflow. Starting at ₹499/month for Indian creators via UPI.",
    },
  ],
  faqs: [
    {
      q: "How is HookCut different from other YouTube Shorts generators?",
      a: "Most Shorts generators clip first and score never. HookCut analyzes the full transcript, scores every potential hook moment from 0 to 100, and only generates Shorts from the top-scoring moments. The result is fewer Shorts with meaningfully higher quality — each one starting with a real scroll-stopping hook.",
    },
    {
      q: "What's included in each generated YouTube Short?",
      a: "Every generated Short is a 9:16 vertical video with auto-embedded captions in your chosen style (Clean, Bold, Neon, or Minimal). The start and end times are based on the hook score analysis, with ±10 second trim controls available before generation.",
    },
    {
      q: "How long does it take to generate a YouTube Short?",
      a: "Hook detection takes under 2 minutes. Short generation typically takes 1–3 minutes per clip after you select your hooks. Most creators have their first Short ready to post within 5 minutes of pasting their YouTube URL.",
    },
    {
      q: "Does HookCut generate Shorts from any YouTube video?",
      a: "Yes — any public YouTube video. Paste the URL and HookCut handles the rest. No file upload, no special access needed.",
    },
    {
      q: "Does the YouTube Shorts generator work for Hindi and regional language videos?",
      a: "Yes. HookCut supports 12+ Indian languages including Hindi, Tamil, Telugu, Kannada, Malayalam, and Hinglish. The hook scoring and Short generation work accurately across all supported languages.",
    },
    {
      q: "Can I try it free before subscribing?",
      a: "Yes. Every new account includes 120 free minutes of analysis and Short generation — no credit card required.",
    },
  ],
};

export default function YouTubeShortsGeneratorPage() {
  return <AlternativePage data={data} />;
}
