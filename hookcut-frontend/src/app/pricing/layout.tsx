import type { Metadata } from "next";


export const metadata: Metadata = {
  title: "HookCut Pricing — Free AI YouTube Shorts Maker | Pro Plans from $9/mo",
  description:
    "Start making YouTube Shorts for free with 120 AI minutes/month. Pro plan: 300 min, watermark-free, priority processing — $9/mo or ₹499/mo. Pay-as-you-go available. No credit card to start.",
  keywords: [
    "youtube shorts maker pricing",
    "AI video clipping tool free",
    "youtube shorts generator price",
    "hookcut pricing",
    "free youtube shorts tool",
  ],
  openGraph: {
    title: "HookCut Pricing — Free YouTube Shorts Maker | Plans from $9/mo",
    description:
      "120 free AI minutes/month. Pro: 300 min, watermark-free, $9/mo. No credit card to start.",
    url: "https://hookcut.ai/pricing",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HookCut Pricing — Free YouTube Shorts Maker",
    description:
      "120 free AI minutes/month. Pro: 300 min, watermark-free, $9/mo. No credit card to start.",
  },
  alternates: { canonical: "https://hookcut.ai/pricing" },
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
