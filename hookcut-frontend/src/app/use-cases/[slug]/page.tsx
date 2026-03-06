import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import { getUseCase, getAllUseCaseSlugs } from "@/lib/use-cases";
import Header from "@/components/header";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  return getAllUseCaseSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const useCase = getUseCase(slug);
  if (!useCase) return { title: "Not Found" };
  return {
    title: useCase.metaTitle,
    description: useCase.metaDescription,
    openGraph: {
      title: useCase.metaTitle,
      description: useCase.metaDescription,
      type: "website",
      url: `https://hookcut.ai/use-cases/${slug}`,
    },
    twitter: { card: "summary_large_image", title: useCase.metaTitle, description: useCase.metaDescription },
    alternates: { canonical: `https://hookcut.ai/use-cases/${slug}` },
  };
}

export default async function UseCasePage({ params }: Props) {
  const { slug } = await params;
  const useCase = getUseCase(slug);
  if (!useCase) notFound();

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "https://hookcut.ai" },
      { "@type": "ListItem", position: 2, name: "Use Cases", item: "https://hookcut.ai/use-cases" },
      { "@type": "ListItem", position: 3, name: useCase.persona, item: `https://hookcut.ai/use-cases/${slug}` },
    ],
  };

  return (
    <div className="bg-[#FAFAF8] min-h-screen">
      <Header />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
      />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#E84A2F] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-3xl mx-auto">
          <nav className="flex items-center gap-2 text-xs text-[#A1A1AA] mb-6" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-[#71717A] transition-colors">Home</Link>
            <span aria-hidden="true">/</span>
            <Link href="/use-cases" className="hover:text-[#71717A] transition-colors">Use Cases</Link>
            <span aria-hidden="true">/</span>
            <span className="text-[#0A0A0A]">{useCase.persona}</span>
          </nav>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#E84A2F]/10 border border-[#E84A2F]/20 text-[#E84A2F] text-xs font-semibold mb-5">
            For {useCase.persona}
          </div>
          <h1 className="text-4xl sm:text-5xl font-[family-name:--font-display] font-bold text-[#0A0A0A] leading-tight tracking-tight mb-4">
            {useCase.headline}
          </h1>
          <p className="text-lg text-[#71717A] leading-relaxed mb-8 max-w-2xl">{useCase.subheadline}</p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
          >
            Start Analyzing Free
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <p className="text-xs text-[#A1A1AA] mt-3">120 free minutes · No credit card required</p>
        </div>
      </section>

      <main id="main-content">
        {/* Pain Points */}
        <section className="py-16 px-6 bg-white border-t border-[#E4E4E7]">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-8">
              The problem with your current workflow
            </h2>
            <ul className="space-y-4" aria-label="Pain points">
              {useCase.painPoints.map((point) => (
                <li key={point} className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-[#DC2626] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span className="text-[#0A0A0A] leading-relaxed">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Solution */}
        <section className="py-16 px-6 bg-[#FAFAF8]">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-4">
              How HookCut solves it
            </h2>
            <p className="text-[#71717A] leading-relaxed text-lg">{useCase.solution}</p>
          </div>
        </section>

        {/* Features */}
        <section className="py-16 px-6 bg-white border-t border-[#E4E4E7]">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-8">
              Key features for {useCase.persona.toLowerCase()}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              {useCase.features.map((feature, i) => (
                <div key={feature.title} className="flex flex-col gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#E84A2F]/10 text-[#E84A2F] flex items-center justify-center font-bold text-sm">
                    {i + 1}
                  </div>
                  <h3 className="font-semibold text-[#0A0A0A]">{feature.title}</h3>
                  <p className="text-[#71717A] text-sm leading-relaxed">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Testimonial */}
        <section className="py-16 px-6 bg-[#0A0A0A]">
          <div className="max-w-2xl mx-auto text-center">
            <svg className="w-8 h-8 text-[#E84A2F] mx-auto mb-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
            </svg>
            <blockquote className="text-xl text-white leading-relaxed mb-6">
              &ldquo;{useCase.testimonial.quote}&rdquo;
            </blockquote>
            <cite className="not-italic">
              <p className="font-semibold text-white">{useCase.testimonial.name}</p>
              <p className="text-white/50 text-sm">{useCase.testimonial.handle} · {useCase.testimonial.subscribers}</p>
            </cite>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-20 px-6 bg-[#FAFAF8] text-center border-t border-[#E4E4E7]">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-3xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-4">
              Ready to find your best hooks?
            </h2>
            <p className="text-[#71717A] mb-8">120 free minutes. No credit card. Results in under 2 minutes.</p>
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
        </section>
      </main>
    </div>
  );
}
