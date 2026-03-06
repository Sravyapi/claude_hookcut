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
    <div className="bg-[#FAFAF8] min-h-screen">
      <Header />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#E84A2F] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      {/* Article header */}
      <header className="pt-32 pb-12 px-6 border-b border-[#E4E4E7] bg-white">
        <div className="max-w-3xl mx-auto">
          <nav className="flex items-center gap-2 text-xs text-[#A1A1AA] mb-6" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-[#71717A] transition-colors">Home</Link>
            <span aria-hidden="true">/</span>
            <Link href={backHref} className="hover:text-[#71717A] transition-colors">{backLabel}</Link>
            <span aria-hidden="true">/</span>
            <span className="text-[#0A0A0A] truncate max-w-[200px]">{frontmatter.title}</span>
          </nav>

          <h1 className="text-3xl sm:text-4xl font-[family-name:--font-display] font-bold text-[#0A0A0A] leading-tight tracking-tight mb-4">
            {frontmatter.title}
          </h1>

          <p className="text-lg text-[#71717A] mb-6 leading-relaxed">{frontmatter.description}</p>

          <div className="flex flex-wrap items-center gap-4 text-sm text-[#A1A1AA]">
            {frontmatter.author && (
              <span>By <strong className="text-[#71717A]">{frontmatter.author}</strong></span>
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
          <div className="prose prose-neutral max-w-none prose-headings:font-[family-name:--font-display] prose-headings:text-[#0A0A0A] prose-p:text-[#71717A] prose-p:leading-relaxed prose-a:text-[#E84A2F] prose-a:no-underline hover:prose-a:underline prose-strong:text-[#0A0A0A] prose-code:text-[#E84A2F] prose-code:bg-[#E84A2F]/8 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:font-normal prose-li:text-[#71717A] prose-blockquote:border-[#E84A2F] prose-blockquote:text-[#71717A] prose-hr:border-[#E4E4E7]">
            {children}
          </div>
        </div>

        {/* CTA */}
        <div className="border-t border-[#E4E4E7] bg-white py-16 px-6 text-center">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-3">
              Find the hooks in your videos
            </h2>
            <p className="text-[#71717A] mb-6">
              120 free minutes. No credit card. Results in under 2 minutes.
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
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
            className="text-sm text-[#71717A] hover:text-[#0A0A0A] transition-colors inline-flex items-center gap-1"
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
