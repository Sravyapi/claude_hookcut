import type { Metadata } from "next";
import { Geist, Geist_Mono, Outfit } from "next/font/google";
import { Providers } from "@/components/providers";
import { ErrorBoundary } from "@/components/error-boundary";
import { Toaster } from "@/components/ui/toaster";
import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "HookCut — Free AI YouTube Shorts Maker | Find Viral Hooks Instantly",
    template: "%s | HookCut",
  },
  description:
    "Turn any YouTube video into viral Shorts in under 2 minutes. HookCut uses AI to find the 5 best hook moments, scores them across 7 dimensions, and exports ready-to-post clips with captions. Free to start.",
  keywords: [
    "youtube shorts maker",
    "AI video clipping tool",
    "youtube shorts generator",
    "video hook finder",
    "AI clip generator",
    "repurpose youtube videos",
    "short form video maker",
    "youtube to shorts converter",
    "viral shorts creator",
    "podcast clip generator",
  ],
  metadataBase: new URL("https://hookcut.ai"),
  openGraph: {
    type: "website",
    siteName: "HookCut",
    title: "HookCut — Free AI YouTube Shorts Maker | Find Viral Hooks",
    description:
      "Paste a YouTube URL. AI finds the 5 best hooks, scores them, and exports Shorts with captions — in under 2 minutes. 120 free minutes, no credit card.",
    url: "https://hookcut.ai",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "HookCut — AI YouTube Shorts Maker" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HookCut — Free AI YouTube Shorts Maker",
    description:
      "Paste a YouTube URL. AI finds the 5 best hooks, scores them, and exports Shorts with captions — in under 2 minutes. Free to start.",
    images: ["/og-image.png"],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`dark ${geist.variable} ${geistMono.variable} ${outfit.variable}`}
    >
      <body className="min-h-screen antialiased font-sans bg-grid">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@graph": [
                {
                  "@type": "Organization",
                  name: "HookCut",
                  url: "https://hookcut.ai",
                  logo: "https://hookcut.ai/og-image.png",
                  description:
                    "AI-powered YouTube Shorts maker that finds viral hook moments, scores them, and exports ready-to-post clips with captions.",
                  foundingDate: "2025",
                  sameAs: [],
                },
                {
                  "@type": "WebSite",
                  name: "HookCut",
                  url: "https://hookcut.ai",
                  potentialAction: {
                    "@type": "SearchAction",
                    target: "https://hookcut.ai/?q={search_term_string}",
                    "query-input": "required name=search_term_string",
                  },
                },
                {
                  "@type": "SoftwareApplication",
                  name: "HookCut",
                  applicationCategory: "MultimediaApplication",
                  operatingSystem: "Web",
                  offers: {
                    "@type": "Offer",
                    price: "0",
                    priceCurrency: "USD",
                    description: "Free tier with 120 AI minutes per month",
                  },
                },
              ],
            }),
          }}
        />
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2 focus:bg-[--color-primary] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
        >
          Skip to content
        </a>
        <Providers>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
