import type { Metadata } from "next";
import Link from "next/link";
import { getAllPosts } from "@/lib/mdx";

export const metadata: Metadata = {
  title: "Creator Case Studies | HookCut",
  description:
    "Real results from creators who used HookCut to find viral hooks in their YouTube videos. Finance, podcast, education, and more.",
  openGraph: {
    title: "Creator Case Studies | HookCut",
    description:
      "Real results from creators who used HookCut to find viral hooks in their YouTube videos.",
    type: "website",
    url: "https://hookcut.ai/case-studies",
  },
  twitter: {
    card: "summary_large_image",
    title: "Creator Case Studies | HookCut",
    description:
      "Real results from creators who used HookCut to find viral hooks in their YouTube videos.",
  },
  alternates: { canonical: "https://hookcut.ai/case-studies" },
};

export default function CaseStudiesPage() {
  const posts = getAllPosts("case-studies");

  return (
    <div className="bg-[#FAFAF8] min-h-screen">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#E84A2F] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      {/* Hero */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E84A2F]/10 text-[#E84A2F] text-xs font-semibold uppercase tracking-wider mb-4">
            Case Studies
          </div>
          <h1 className="text-4xl sm:text-5xl font-[family-name:--font-display] font-bold text-[#0A0A0A] leading-tight tracking-tight mb-4">
            Real results from real creators
          </h1>
          <p className="text-lg text-[#71717A] leading-relaxed max-w-2xl">
            How creators across niches and languages used HookCut to find the moments
            in their videos most likely to go viral — and what happened next.
          </p>
        </div>
      </section>

      <main id="main-content">
        {/* Case Study Cards */}
        <section className="pb-24 px-6">
          <div className="max-w-3xl mx-auto">
            {posts.length === 0 ? (
              <p className="text-[#71717A] text-center py-12">
                Case studies coming soon.
              </p>
            ) : (
              <div className="space-y-6">
                {posts.map((post) => (
                  <Link
                    key={post.slug}
                    href={`/case-studies/${post.slug}`}
                    className="block p-6 rounded-xl border border-[#E4E4E7] bg-white hover:border-[#E84A2F]/30 hover:shadow-sm transition-all group"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-3">
                          {post.niche && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#E84A2F]/10 text-[#E84A2F]">
                              {post.niche}
                            </span>
                          )}
                          {post.result && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#16A34A]/10 text-[#16A34A] font-[family-name:--font-mono]">
                              {post.result}
                            </span>
                          )}
                        </div>
                        <h2 className="text-lg font-semibold text-[#0A0A0A] leading-snug mb-2 group-hover:text-[#E84A2F] transition-colors">
                          {post.title}
                        </h2>
                        <p className="text-sm text-[#71717A] leading-relaxed line-clamp-2">
                          {post.description}
                        </p>
                        <div className="flex items-center gap-4 mt-4 text-xs text-[#A1A1AA]">
                          {post.creator && (
                            <span>{post.creator}</span>
                          )}
                          {post.subscribers && (
                            <span>{post.subscribers} subscribers</span>
                          )}
                          {post.readingTime && (
                            <span>{post.readingTime} read</span>
                          )}
                        </div>
                      </div>
                      <svg
                        className="w-5 h-5 text-[#A1A1AA] group-hover:text-[#E84A2F] shrink-0 transition-colors mt-1"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* CTA */}
        <section className="py-20 px-6 bg-[#0A0A0A] text-center">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-3xl font-[family-name:--font-display] font-bold text-white mb-4">
              Your result could be next
            </h2>
            <p className="text-[#A1A1AA] mb-8">
              120 free minutes. No credit card. Results in under 2 minutes.
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
            >
              Find My Hooks
              <svg
                className="w-4 h-4"
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
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}
