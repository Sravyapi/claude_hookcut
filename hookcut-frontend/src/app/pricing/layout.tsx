import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "HookCut Pricing — Start Free, ₹499/month | HookCut",
  description:
    "Choose your HookCut plan. Start with 120 free minutes. Starter at ₹499/mo, Pro at ₹999/mo. AI-powered YouTube hook detection and Shorts generation for Indian creators.",
  openGraph: {
    title: "HookCut Pricing — Start Free, ₹499/month",
    description:
      "Choose your HookCut plan. Start with 120 free minutes. AI-powered YouTube Shorts generation.",
    url: "https://hookcut.ai/pricing",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HookCut Pricing — Start Free, ₹499/month",
    description:
      "Choose your HookCut plan. Start with 120 free minutes. AI-powered YouTube Shorts generation.",
  },
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
