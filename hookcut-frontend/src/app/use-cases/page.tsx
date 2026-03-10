import type { Metadata } from "next";
import Link from "next/link";
import { USE_CASES } from "@/lib/use-cases";
import Header from "@/components/header";

export const metadata: Metadata = {
  title: "HookCut Use Cases | HookCut",
  description:
    "How YouTube creators, podcasters, coaches, and educators use HookCut to find viral hook moments and turn them into Shorts.",
  openGraph: {
    title: "HookCut Use Cases | HookCut",
    description:
      "How YouTube creators, podcasters, coaches, and educators use HookCut to find viral hook moments.",
    type: "website",
    url: "https://hookcut.ai/use-cases",
  },
  twitter: {
    card: "summary_large_image",
    title: "HookCut Use Cases | HookCut",
    description:
      "How YouTube creators, podcasters, coaches, and educators use HookCut to find viral hook moments.",
  },
  alternates: { canonical: "https://hookcut.ai/use-cases" },
};

export default function UseCasesIndexPage() {
  return (
    <div className="bg-[var(--color-bg)] min-h-screen">
      <Header />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[var(--color-primary)] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      <section className="pt-32 pb-16 px-6 text-center">
        <div className="max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/20 text-[var(--color-primary)] text-xs font-semibold uppercase tracking-wider mb-6">
            Use Cases
          </div>
          <h1 className="text-h1 font-[family-name:--font-display] font-bold text-[var(--color-text)] mb-4">
            HookCut works for every creator
          </h1>
          <p className="text-[var(--color-muted)] text-lg">
            Whether you make YouTube videos, run a podcast, teach online, or build your
            brand — HookCut finds the moments that stop the scroll.
          </p>
        </div>
      </section>

      <main id="main-content" className="pb-24 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="space-y-4">
            {USE_CASES.map((useCase) => (
              <Link
                key={useCase.slug}
                href={`/use-cases/${useCase.slug}`}
                className="block glass-card glass-hover rounded-2xl p-6 group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="inline-flex items-center px-2.5 py-1 rounded-full bg-[var(--color-primary)]/10 text-[var(--color-primary)] text-xs font-semibold mb-3">
                      {useCase.persona}
                    </div>
                    <h2 className="text-xl font-[family-name:--font-display] font-bold text-[var(--color-text)] group-hover:text-[var(--color-primary)] transition-colors mb-2 leading-snug">
                      {useCase.headline}
                    </h2>
                    <p className="text-[var(--color-muted)] text-sm leading-relaxed">
                      {useCase.subheadline}
                    </p>
                  </div>
                  <svg
                    className="w-5 h-5 text-[var(--color-muted)] group-hover:text-[var(--color-primary)] transition-colors shrink-0 mt-1"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 7l5 5m0 0l-5 5m5-5H6"
                    />
                  </svg>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
