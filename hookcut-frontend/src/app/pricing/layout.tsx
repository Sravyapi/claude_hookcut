import type { Metadata } from "next";


export const metadata: Metadata = {
  title: "Pricing — Start Free, Upgrade Anytime",
  description:
    "Choose your HookCut plan. Start with 120 free minutes. Affordable Lite and Pro plans for creators. AI-powered YouTube hook detection and Shorts generation.",
  openGraph: {
    title: "Pricing — Start Free, Upgrade Anytime",
    description:
      "Choose your HookCut plan. Start with 120 free minutes. AI-powered YouTube Shorts generation.",
    url: "https://hookcut.ai/pricing",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Pricing — Start Free, Upgrade Anytime",
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
