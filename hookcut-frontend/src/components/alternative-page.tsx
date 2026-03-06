import Link from "next/link";
import Header from "@/components/header";

export interface CompetitorData {
  competitor: string;
  competitorSlug: string;
  headline: string;
  intro: string;
  tableRows: {
    feature: string;
    hookcut: string;
    competitor: string;
    hookcutWins: boolean;
  }[];
  reasons: { title: string; description: string }[];
  faqs: { q: string; a: string }[];
}

export function AlternativePage({ data }: { data: CompetitorData }) {
  return (
    <div className="bg-[#FAFAF8] min-h-screen">
      <Header />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#E84A2F] focus:text-white focus:rounded-lg focus:text-sm focus:font-medium"
      >
        Skip to content
      </a>

      {/* Hero */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-3xl mx-auto">
          <nav className="flex items-center gap-2 text-xs text-[#A1A1AA] mb-6" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-[#71717A] transition-colors">Home</Link>
            <span aria-hidden="true">/</span>
            <span className="text-[#0A0A0A]">vs {data.competitor}</span>
          </nav>
          <h1 className="text-4xl sm:text-5xl font-[family-name:--font-display] font-bold text-[#0A0A0A] leading-tight tracking-tight mb-4">
            {data.headline}
          </h1>
          <p className="text-lg text-[#71717A] leading-relaxed mb-8 max-w-2xl">{data.intro}</p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
          >
            Try HookCut Free
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <p className="text-xs text-[#A1A1AA] mt-3">120 free minutes · No credit card required</p>
        </div>
      </section>

      <main id="main-content">
        {/* Comparison Table */}
        <section className="py-16 px-6 bg-white">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-8">
              HookCut vs {data.competitor}: Feature comparison
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#E4E4E7]">
                    <th className="text-left py-3 pr-6 text-[#A1A1AA] font-semibold text-xs uppercase tracking-wider">Feature</th>
                    <th className="text-center py-3 px-4 text-[#E84A2F] font-semibold text-xs uppercase tracking-wider">HookCut</th>
                    <th className="text-center py-3 px-4 text-[#71717A] font-semibold text-xs uppercase tracking-wider">{data.competitor}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.tableRows.map((row) => (
                    <tr key={row.feature} className="border-b border-[#F4F4F5]">
                      <td className="py-3 pr-6 text-[#0A0A0A] font-medium">{row.feature}</td>
                      <td className="py-3 px-4 text-center">
                        <span className={row.hookcutWins ? "text-[#16A34A] font-semibold" : "text-[#71717A]"}>
                          {row.hookcut}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center text-[#71717A]">{row.competitor}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* 3 Reasons */}
        <section className="py-16 px-6 bg-[#FAFAF8]">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-8">
              3 reasons to switch to HookCut
            </h2>
            <div className="space-y-6">
              {data.reasons.map((reason, i) => (
                <div key={reason.title} className="flex gap-5">
                  <div className="shrink-0 w-8 h-8 rounded-full bg-[#E84A2F] text-white flex items-center justify-center text-sm font-bold">
                    {i + 1}
                  </div>
                  <div>
                    <h3 className="font-semibold text-[#0A0A0A] mb-2">{reason.title}</h3>
                    <p className="text-[#71717A] leading-relaxed text-sm">{reason.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA mid-page */}
        <section className="py-12 px-6 bg-[#0A0A0A] text-center">
          <div className="max-w-xl mx-auto">
            <p className="text-white font-semibold mb-4">
              Ready to find hooks that actually stop the scroll?
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
            >
              Start Free with HookCut
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </section>

        {/* FAQ with JSON-LD */}
        <section className="py-16 px-6 bg-white">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-8">
              Frequently asked questions
            </h2>
            <dl className="space-y-6">
              {data.faqs.map((faq) => (
                <div key={faq.q} className="border-b border-[#E4E4E7] pb-6 last:border-0 last:pb-0">
                  <dt className="font-semibold text-[#0A0A0A] mb-2">{faq.q}</dt>
                  <dd className="text-[#71717A] leading-relaxed text-sm">{faq.a}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-20 px-6 bg-[#FAFAF8] text-center">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-3xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-4">
              Try HookCut free today
            </h2>
            <p className="text-[#71717A] mb-8">120 free minutes. No credit card. Results in under 2 minutes.</p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
            >
              Find My Hooks
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
