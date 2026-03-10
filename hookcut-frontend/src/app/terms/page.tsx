import Link from "next/link";
import Header from "@/components/header";

export const metadata = {
  title: "Terms of Service — HookCut",
  description: "Terms of Service for HookCut by NyxPath. Read the full terms governing your use of the HookCut platform.",
};

const SECTIONS = [
  {
    heading: "1. Acceptance of Terms",
    body: "By accessing or using HookCut, you agree to be bound by these Terms of Service. If you do not agree, please do not use the service.",
  },
  {
    heading: "2. Use of Service",
    body: "HookCut allows you to analyze YouTube videos and generate short-form content using AI. You must provide valid YouTube URLs and may only process content you have the right to use. You are responsible for all content generated through your account.",
  },
  {
    heading: "3. Credits & Payments",
    body: "HookCut operates on a credit-minute system. Credits are deducted based on the duration of the source video analyzed. Free accounts receive 5 minutes per month. Paid plans and pay-as-you-go credits are available. Pay-as-you-go credits do not expire. Subscription credits reset at the start of each billing period. All payments are processed securely. Refunds are handled on a case-by-case basis — contact support.",
  },
  {
    heading: "4. Prohibited Uses",
    body: "You may not use HookCut to process content that infringes third-party intellectual property rights, contains illegal material, or violates YouTube's Terms of Service. Automated abuse of the platform (scripted bulk requests, credential stuffing, etc.) is prohibited.",
  },
  {
    heading: "5. Limitation of Liability",
    body: "HookCut is provided \"as is\" without warranties of any kind. NyxPath shall not be liable for indirect, incidental, or consequential damages arising from your use of the service. Our maximum aggregate liability is limited to the amount you paid us in the 30 days preceding the claim.",
  },
  {
    heading: "6. Governing Law",
    body: "These Terms are governed by the laws of India. Any disputes shall be subject to the exclusive jurisdiction of courts in India.",
  },
  {
    heading: "7. Contact",
    body: "For questions about these Terms, contact us at support@hookcut.nyxpath.com.",
  },
];

export default function TermsPage() {
  return (
    <>
      <Header />
      <main className="pt-24 pb-16">
        {/* Background orbs */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-[var(--color-primary)]/[0.05] blur-[140px]" />
          <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full bg-[var(--color-primary)]/[0.04] blur-[120px]" />
        </div>

        <div className="relative max-w-2xl mx-auto px-6">
          {/* Header */}
          <div className="mb-10">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-[var(--color-primary)] flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-[var(--color-primary)]/25">
                H
              </div>
              <span className="text-sm text-white/40 font-medium">HookCut by NyxPath</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Terms of Service</h1>
            <p className="text-sm text-white/35">
              Last updated: March 2026 — Full terms in effect. Contact{" "}
              <a
                href="mailto:support@hookcut.nyxpath.com"
                className="text-[var(--color-primary)]/80 hover:text-[var(--color-primary)] underline transition-colors"
              >
                support@hookcut.nyxpath.com
              </a>{" "}
              for questions.
            </p>
          </div>

          {/* Glass card */}
          <div className="glass-card rounded-2xl p-8">
            <div className="prose prose-invert prose-sm md:prose-base max-w-none space-y-8">
              {SECTIONS.map((section) => (
                <section key={section.heading} aria-labelledby={section.heading}>
                  <h2 className="text-base font-semibold text-white mb-2">
                    {section.heading}
                  </h2>
                  <p className="text-sm text-white/55 leading-relaxed">
                    {section.body}
                  </p>
                </section>
              ))}
            </div>
          </div>

          {/* Back link */}
          <div className="mt-8 text-center">
            <Link
              href="/"
              className="text-sm text-[var(--color-primary)]/70 hover:text-[var(--color-primary)] transition-colors"
            >
              ← Back to home
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}
