import Link from "next/link";
import type { PostFrontmatter } from "@/lib/mdx";
import Header from "@/components/header";

interface BlogLayoutProps {
  frontmatter: PostFrontmatter;
  children: React.ReactNode;
  type?: "blog" | "case-studies";
}

export function BlogLayout({ frontmatter, children, type = "blog" }: BlogLayoutProps) {
  const backHref = type === "blog" ? "/blog" : "/case-studies";
  const backLabel = type === "blog" ? "All Articles" : "All Case Studies";

  return (
    <div className="bg-[var(--color-bg)] min-h-screen">
      <Header />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#E84A2F] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      {/* Article header */}
      <header className="pt-32 pb-12 px-6 border-b border-[var(--color-border-def)]">
        <div className="max-w-3xl mx-auto">
          <nav className="flex items-center gap-2 text-xs text-[var(--color-muted)] mb-6" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-[var(--color-text)] transition-colors">Home</Link>
            <span aria-hidden="true">/</span>
            <Link href={backHref} className="hover:text-[var(--color-text)] transition-colors">{backLabel}</Link>
            <span aria-hidden="true">/</span>
            <span className="text-[var(--color-text)] truncate max-w-[200px]">{frontmatter.title}</span>
          </nav>

          <h1 className="text-3xl sm:text-4xl font-[family-name:--font-display] font-bold text-[var(--color-text)] leading-tight tracking-tight mb-4">
            {frontmatter.title}
          </h1>

          <p className="text-lg text-[var(--color-muted)] mb-6 leading-relaxed">{frontmatter.description}</p>

          <div className="flex flex-wrap items-center gap-4 text-sm text-[var(--color-muted)]">
            {frontmatter.author && (
              <span>By <strong className="text-[var(--color-text)]">{frontmatter.author}</strong></span>
            )}
            <span>
              {new Date(frontmatter.date).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
            {frontmatter.readingTime && <span>{frontmatter.readingTime} read</span>}
          </div>
        </div>
      </header>

      {/* Content */}
      <main id="main-content">
        <div className="max-w-3xl mx-auto px-6 py-12">
          <div className="prose prose-invert prose-lg max-w-none prose-headings:font-[family-name:--font-display] prose-headings:text-[var(--color-text)] prose-p:text-[var(--color-muted)] prose-p:leading-relaxed prose-a:text-[#E84A2F] prose-a:no-underline hover:prose-a:underline prose-strong:text-[var(--color-text)] prose-code:text-[#E84A2F] prose-code:bg-[#E84A2F]/8 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:font-normal prose-li:text-[var(--color-muted)] prose-blockquote:border-[#E84A2F] prose-blockquote:text-[var(--color-muted)] prose-hr:border-[var(--color-border-def)]">
            {children}
          </div>
        </div>

        {/* CTA */}
        <div className="border-t border-[var(--color-border-def)] bg-[var(--color-surface-1)] py-16 px-6 text-center">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[var(--color-text)] mb-3">
              Find the hooks in your videos
            </h2>
            <p className="text-[var(--color-muted)] mb-6">
              120 free minutes. No credit card. Results in under 2 minutes.
            </p>
            <Link
              href="/"
              className="btn-primary inline-flex items-center gap-2 text-sm"
            >
              Start Analyzing Free
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>

        <div className="py-8 px-6 text-center">
          <Link
            href={backHref}
            className="text-sm text-[var(--color-muted)] hover:text-[var(--color-text)] transition-colors inline-flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
            </svg>
            {backLabel}
          </Link>
        </div>
      </main>
    </div>
  );
}
