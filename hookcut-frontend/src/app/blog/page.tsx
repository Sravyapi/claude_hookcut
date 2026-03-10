import type { Metadata } from "next";
import Link from "next/link";
import { getAllPosts } from "@/lib/mdx";
import Header from "@/components/header";
import AuthRedirect from "@/components/auth-redirect";

export const metadata: Metadata = {
  title: "HookCut Blog — Creator Tips, Hook Strategy | HookCut",
  description:
    "Insights on YouTube hook strategy, viral Shorts creation, and AI-powered content analysis from the HookCut team.",
  openGraph: {
    title: "HookCut Blog — Creator Tips, Hook Strategy | HookCut",
    description:
      "Insights on YouTube hook strategy, viral Shorts creation, and AI-powered content analysis from the HookCut team.",
    type: "website",
    url: "https://hookcut.ai/blog",
  },
  twitter: {
    card: "summary_large_image",
    title: "HookCut Blog — Creator Tips, Hook Strategy | HookCut",
    description:
      "Insights on YouTube hook strategy, viral Shorts creation, and AI-powered content analysis from the HookCut team.",
  },
  alternates: { canonical: "https://hookcut.ai/blog" },
};

export default function BlogIndexPage() {
  const posts = getAllPosts("blog");

  return (
    <div className="bg-[var(--color-bg)] min-h-screen">
      <AuthRedirect />
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
            HookCut Blog
          </div>
          <h1 className="text-h1 font-[family-name:--font-display] font-bold text-[var(--color-text)] mb-4">
            Hook strategy for creators
          </h1>
          <p className="text-[var(--color-muted)] text-lg">
            Research, tactics, and insights to help you create Shorts that stop the scroll.
          </p>
        </div>
      </section>

      <main id="main-content" className="pb-24 px-6">
        <div className="max-w-3xl mx-auto">
          {posts.length === 0 ? (
            <p className="text-center text-[var(--color-muted)] py-16">No posts yet. Check back soon.</p>
          ) : (
            <div className="space-y-6">
              {posts.map((post) => (
                <Link
                  key={post.slug}
                  href={`/blog/${post.slug}`}
                  className="block glass-card glass-hover rounded-2xl p-6 group"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-[family-name:--font-display] font-bold text-[var(--color-text)] group-hover:text-[var(--color-primary)] transition-colors mb-2 leading-snug">
                        {post.title}
                      </h2>
                      <p className="text-[var(--color-muted)] text-sm leading-relaxed mb-4">{post.description}</p>
                      <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--color-muted)]">
                        <span>
                          {new Date(post.date).toLocaleDateString("en-US", {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </span>
                        {post.readingTime && <span>{post.readingTime} read</span>}
                      </div>
                    </div>
                    <svg
                      className="w-5 h-5 text-[var(--color-muted)] group-hover:text-[var(--color-primary)] transition-colors shrink-0 mt-1"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
