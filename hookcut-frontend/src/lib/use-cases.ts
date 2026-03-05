export interface UseCase {
  slug: string;
  persona: string;
  headline: string;
  subheadline: string;
  painPoints: string[];
  solution: string;
  features: { title: string; description: string }[];
  testimonial: { quote: string; name: string; handle: string; subscribers: string };
  metaTitle: string;
  metaDescription: string;
}

export const USE_CASES: UseCase[] = [
  {
    slug: "youtube-creators",
    persona: "YouTube Creators",
    headline: "Turn your long videos into Shorts that actually stop the scroll.",
    subheadline:
      "You spend hours creating long-form content. HookCut finds the 5 moments most likely to go viral — and clips them for you.",
    painPoints: [
      "Manually scrubbing 30-minute videos to find clip-worthy moments takes hours",
      "Most clips you pick get fewer than 1,000 views",
      "Other AI tools give you 10 clips — and 9 of them are filler",
    ],
    solution:
      "HookCut analyzes your video's transcript and surfaces the top 5 hook moments, scored by engagement potential. You pick up to 3, choose a caption style, and download — ready to post.",
    features: [
      { title: "Hook Score (0–10)", description: "Every moment is scored so you know which clips are worth posting." },
      { title: "18 Hook Type Classifications", description: "Curiosity gaps, shock statistics, open loops — know what kind of hook you're posting before you post it." },
      { title: "One-click Short generation", description: "9:16 vertical video with burnt-in captions. No editor required." },
    ],
    testimonial: {
      quote:
        "I went from 800 to 14,000 views per Short after using HookCut. The hook score is the feature I didn't know I needed.",
      name: "Arjun Mehta",
      handle: "@techwitharjun",
      subscribers: "47K subscribers",
    },
    metaTitle: "HookCut for YouTube Creators | Find Viral Hooks in Your Videos",
    metaDescription:
      "YouTube creators use HookCut to find the hook moments most likely to go viral — scored, clipped, and ready to post as Shorts in under 2 minutes.",
  },
  {
    slug: "podcast-to-shorts",
    persona: "Podcasters",
    headline: "Your best podcast moments are already going viral — you just haven't found them yet.",
    subheadline:
      "HookCut scans your full episode and finds the moments most likely to stop a scroll. No manual editing required.",
    painPoints: [
      "2-hour podcast episodes have maybe 5 viral-worthy moments — finding them takes all day",
      "Most podcast clips lead with introductions that viewers skip immediately",
      "Manually transcribing and reviewing every exchange is not sustainable",
    ],
    solution:
      "Paste your podcast's YouTube URL. HookCut reads the entire transcript, detects the highest-engagement moments, and turns them into 9:16 Shorts with captions. Your audience on Reels and Shorts can discover your podcast without subscribing first.",
    features: [
      { title: "Full-episode analysis", description: "Works on 3-hour episodes just as well as 30-minute ones. No length limit." },
      { title: "Clip boundary trimming", description: "Fine-tune start and end points ±10 seconds after seeing the hook score." },
      { title: "Hinglish and multilingual support", description: "Hindi, English, Tamil, Telugu, and 8 more languages supported." },
    ],
    testimonial: {
      quote:
        "I found the exact moment in a 45-minute interview that got 2M views as a Short. HookCut saved me 4 hours of manual review.",
      name: "Ravi Shankar",
      handle: "@financewithravi",
      subscribers: "128K subscribers",
    },
    metaTitle: "HookCut for Podcasters | Turn Episodes into Viral Shorts",
    metaDescription:
      "Podcasters use HookCut to find the best moments in their episodes and turn them into YouTube Shorts and Instagram Reels — automatically.",
  },
  {
    slug: "coaches-and-consultants",
    persona: "Coaches & Consultants",
    headline: "Your expertise deserves to be seen. HookCut makes sure it is.",
    subheadline:
      "You create content to build authority. HookCut finds the moments that demonstrate it — and makes them impossible to scroll past.",
    painPoints: [
      "Your best insights get buried in the middle of long explainer videos",
      "You don't have time to edit — you need to focus on clients",
      "Generic AI tools clip intros and Q&A sections that don't convert",
    ],
    solution:
      "HookCut identifies the moments in your educational videos where your authority shines — contrarian claims, key insights, surprising statistics. These are exactly the moments that build audiences. HookCut clips them, captions them, and delivers them for posting.",
    features: [
      { title: "Contrarian & insight hook detection", description: "HookCut specializes in the hook types that work best for educational creators." },
      { title: "Platform Dynamics insights", description: "Each hook comes with notes on which platform it's best suited for — Reels, Shorts, or TikTok." },
      { title: "Batch generation", description: "Select up to 3 hooks per video and generate all Shorts in one submission." },
    ],
    testimonial: {
      quote:
        "I post one Short per day now with zero manual editing. My consulting inquiries went up 40% in 60 days.",
      name: "Priya Nair",
      handle: "@learnwithpriya",
      subscribers: "22K subscribers",
    },
    metaTitle: "HookCut for Coaches & Consultants | Turn Expertise into Viral Clips",
    metaDescription:
      "Coaches and consultants use HookCut to find the authority-building moments in their videos and turn them into Shorts that attract clients.",
  },
  {
    slug: "repurpose-content",
    persona: "Content Repurposers",
    headline: "Every piece of long-form content is a Shorts library waiting to be unlocked.",
    subheadline:
      "Webinars, interviews, conference talks, tutorials — HookCut extracts the scroll-stopping moments from any long-form YouTube video.",
    painPoints: [
      "You have months of archival content with 0 Shorts extracted from any of it",
      "Most repurposing tools are designed for fresh content — not 60-minute conference talks",
      "Hiring a video editor to find and clip hooks costs $50–200 per video",
    ],
    solution:
      "Paste any YouTube URL — including videos from your archive. HookCut doesn't care if the video is a week old or three years old. It analyzes the transcript, finds the hooks, and generates the Shorts.",
    features: [
      { title: "Archive-friendly analysis", description: "Works on any public YouTube video, regardless of upload date or length." },
      { title: "Transparent credit billing", description: "Credits deducted per minute of video analyzed — not per video. Short videos cost less." },
      { title: "Instant download links", description: "Download links ready within 2 minutes of submission. Valid for 24 hours." },
    ],
    testimonial: {
      quote:
        "I processed 30 old webinar recordings in one afternoon. HookCut turned 90 hours of archival content into 150 Shorts in a weekend.",
      name: "Suresh Kumar",
      handle: "@contentwithoutstress",
      subscribers: "15K subscribers",
    },
    metaTitle: "HookCut for Content Repurposing | Turn Any Video into Viral Shorts",
    metaDescription:
      "Repurpose any long-form YouTube video into viral Shorts with HookCut. Works on webinars, interviews, tutorials, and archive content.",
  },
];

export function getUseCase(slug: string): UseCase | undefined {
  return USE_CASES.find((uc) => uc.slug === slug);
}

export function getAllUseCaseSlugs(): string[] {
  return USE_CASES.map((uc) => uc.slug);
}
