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
    default: "HookCut — Find the Hook. Stop the Scroll.",
    template: "%s | HookCut",
  },
  description:
    "Paste any YouTube URL. HookCut identifies the moments most likely to stop a scroll — scored, explained, and ready to post as Shorts.",
  metadataBase: new URL("https://hookcut.ai"),
  openGraph: {
    type: "website",
    siteName: "HookCut",
    title: "HookCut — Find the Hook. Stop the Scroll.",
    description:
      "Paste any YouTube URL. HookCut identifies the moments most likely to stop a scroll — scored, explained, and ready to post as Shorts.",
    url: "https://hookcut.ai",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "HookCut" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HookCut — Find the Hook. Stop the Scroll.",
    description:
      "Paste any YouTube URL. HookCut identifies the moments most likely to stop a scroll — scored, explained, and ready to post as Shorts.",
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
      <body className="min-h-screen antialiased font-sans">
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
