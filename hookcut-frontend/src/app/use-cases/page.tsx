import type { Metadata } from "next";
import Link from "next/link";
import { USE_CASES } from "@/lib/use-cases";
import Header from "@/components/header";

export const metadata: Metadata = {
  title: "Use Cases | HookCut — Hook Analysis for Every Creator",
  description:
    "How YouTube creators, podcasters, coaches, and educators use HookCut to find viral hook moments and turn them into Shorts.",
  openGraph: {
    title: "Use Cases | HookCut",
    description:
      "How YouTube creators, podcasters, coaches, and educators use HookCut to find viral hook moments.",
    type: "website",
    url: "https://hookcut.ai/use-cases",
  },
  twitter: {
    card: "summary_large_image",
    title: "Use Cases | HookCut",
    description:
      "How YouTube creators, podcasters, coaches, and educators use HookCut to find viral hook moments.",
  },
  alternates: { canonical: "https://hookcut.ai/use-cases" },
};

export default function UseCasesIndexPage() {
  return (
    <div className="bg-[#FAFAF8] min-h-screen">
      <Header />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#E84A2F] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      <section className="pt-32 pb-16 px-6 text-center">
        <div className="max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#E84A2F]/8 border border-[#E84A2F]/20 text-[#E84A2F] text-xs font-semibold uppercase tracking-wider mb-6">
            Use Cases
          </div>
          <h1 className="text-4xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-4">
            HookCut works for every creator
          </h1>
          <p className="text-[#71717A] text-lg">
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
                className="block bg-white rounded-2xl border border-[#E4E4E7] p-6 hover:border-[#D4D4D8] hover:shadow-sm transition-all group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="inline-flex items-center px-2.5 py-1 rounded-full bg-[#E84A2F]/8 text-[#E84A2F] text-xs font-semibold mb-3">
                      {useCase.persona}
                    </div>
                    <h2 className="text-xl font-[family-name:--font-display] font-bold text-[#0A0A0A] group-hover:text-[#E84A2F] transition-colors mb-2 leading-snug">
                      {useCase.headline}
                    </h2>
                    <p className="text-[#71717A] text-sm leading-relaxed">
                      {useCase.subheadline}
                    </p>
                  </div>
                  <svg
                    className="w-5 h-5 text-[#D4D4D8] group-hover:text-[#E84A2F] transition-colors shrink-0 mt-1"
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
