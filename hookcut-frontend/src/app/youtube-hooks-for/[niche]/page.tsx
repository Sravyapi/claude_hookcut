import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import Header from "@/components/header";
import { nichePages } from "@/lib/niche-pages";

interface Props {
  params: Promise<{ niche: string }>;
}

export const dynamic = "force-static";

export async function generateStaticParams() {
  return nichePages.map((p) => ({ niche: p.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { niche } = await params;
  const page = nichePages.find((p) => p.slug === niche);
  if (!page) return { title: "Not Found" };

  return {
    title: page.metaTitle,
    description: page.metaDescription,
    openGraph: {
      title: page.metaTitle,
      description: page.metaDescription,
      type: "website",
      url: `https://hookcut.ai/youtube-hooks-for/${niche}`,
    },
    twitter: { card: "summary_large_image", title: page.metaTitle, description: page.metaDescription },
    alternates: { canonical: `https://hookcut.ai/youtube-hooks-for/${niche}` },
  };
}

export default async function NichePage({ params }: Props) {
  const { niche } = await params;
  const page = nichePages.find((p) => p.slug === niche);
  if (!page) notFound();

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "https://hookcut.ai" },
      { "@type": "ListItem", position: 2, name: `${page.niche} Hooks`, item: `https://hookcut.ai/youtube-hooks-for/${niche}` },
    ],
  };

  const softwareJsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "HookCut",
    "applicationCategory": "MultimediaApplication",
    "operatingSystem": "Web",
    "offers": { "@type": "Offer", "price": "0", "priceCurrency": "INR" },
    "description": `AI-powered YouTube hook detection for ${page.niche} creators`
  };

  return (
    <div className="bg-[var(--color-bg)] min-h-screen">
      <Header />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareJsonLd) }}
      />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[var(--color-primary)] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      {/* Hero */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-3xl mx-auto">
          <nav className="flex items-center gap-2 text-xs text-[var(--color-muted)] mb-6" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-[var(--color-text)] transition-colors">Home</Link>
            <span aria-hidden="true">/</span>
            <span className="text-[var(--color-text)]">YouTube Hooks for {page.niche}</span>
          </nav>
          <h1 className="text-h1 font-[family-name:--font-display] font-bold text-[var(--color-text)] leading-tight tracking-tight mb-5">
            YouTube Hook Ideas for {page.niche} Creators
          </h1>
          <p className="text-lg text-[var(--color-muted)] leading-relaxed max-w-2xl mb-8">{page.intro}</p>
          <Link
            href="/"
            className="btn-primary inline-flex items-center gap-2 text-sm"
          >
            Find hooks in your {page.niche.toLowerCase()} videos
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
        </div>
      </section>

      <main id="main-content">
        {/* Hook types */}
        <section className="py-16 px-6">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-h2 font-[family-name:--font-display] font-bold text-[var(--color-text)] mb-8">
              5 hook types that work best in {page.niche.toLowerCase()}
            </h2>
            <div className="space-y-5">
              {page.hookTypes.map((hook, i) => (
                <div key={hook.type} className="glass-card glass-hover rounded-2xl p-5 flex gap-4">
                  <div className="shrink-0 w-8 h-8 rounded-full bg-[var(--color-primary)] text-white flex items-center justify-center text-sm font-bold">
                    {i + 1}
                  </div>
                  <div>
                    <h3 className="font-semibold text-[var(--color-text)] mb-1">{hook.type}</h3>
                    <p className="text-[var(--color-muted)] text-sm leading-relaxed">{hook.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Why videos fail */}
        <section className="py-16 px-6 bg-[var(--color-surface-1)]">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-h2 font-[family-name:--font-display] font-bold text-[var(--color-text)] mb-4">
              Why {page.niche.toLowerCase()} videos fail to hook viewers
            </h2>
            <p className="text-[var(--color-muted)] leading-relaxed text-lg">{page.failureReason}</p>
          </div>
        </section>

        {/* HookCut CTA section */}
        <section className="py-16 px-6">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-h2 font-[family-name:--font-display] font-bold text-[var(--color-text)] mb-4">
              Find hooks in your {page.niche.toLowerCase()} videos automatically
            </h2>
            <p className="text-[var(--color-muted)] leading-relaxed mb-6">
              Instead of manually reviewing your videos to find hook moments, HookCut analyzes your transcript and
              surfaces the top 5 hook opportunities — scored by engagement potential. Paste any YouTube URL and get
              results in under 2 minutes.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              {[
                { label: "Paste URL", detail: "Any public YouTube video" },
                { label: "Get scored hooks", detail: "Top 5 moments, scored 0–10" },
                { label: "Download Shorts", detail: "9:16, captions included" },
              ].map((step, i) => (
                <div key={step.label} className="glass-card glass-hover rounded-xl p-4 flex flex-col gap-1.5">
                  <span className="text-[var(--color-primary)] font-bold text-sm">0{i + 1}</span>
                  <span className="font-semibold text-[var(--color-text)] text-sm">{step.label}</span>
                  <span className="text-[var(--color-muted)] text-xs">{step.detail}</span>
                </div>
              ))}
            </div>
            <Link
              href="/"
              className="btn-primary inline-flex items-center gap-2 text-sm"
            >
              Start Free — 120 minutes included
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}
