import Link from "next/link";
import Header from "@/components/header";

export const metadata = {
  title: "Privacy Policy — HookCut",
  description: "Privacy Policy for HookCut by NyxPath. Learn how we collect, use, and protect your data under DPDPA.",
};

const SECTIONS = [
  {
    heading: "1. Information We Collect",
    body: "We collect information you provide when creating an account (name, email address via Google OAuth) and information generated through your use of the service (YouTube URLs submitted, analysis sessions, generated Shorts, credit usage history). We also collect standard server logs (IP address, browser type, request timestamps) for security and debugging.",
  },
  {
    heading: "2. How We Use It",
    body: "We use your information to provide and improve the HookCut service, process payments, send transactional emails (receipts, account notices), detect and prevent abuse, and aggregate anonymized usage statistics to improve our AI models. We do not sell your personal data to third parties.",
  },
  {
    heading: "3. Data Storage",
    body: "Your account data and session history are stored in Supabase PostgreSQL hosted in the ap-south-1 (Mumbai, India) region. Generated video files are stored temporarily and deleted after download or 24 hours, whichever comes first. Backups are encrypted at rest.",
  },
  {
    heading: "4. Third-Party Services",
    body: "HookCut integrates with the following third-party services: Google OAuth (authentication), Razorpay (payment processing — your card details are handled by Razorpay, not stored by us), PostHog (product analytics — anonymized usage events), and Sentry (error monitoring). Each provider's own privacy policy governs their data handling.",
  },
  {
    heading: "5. Your Rights (DPDPA)",
    body: "Under India's Digital Personal Data Protection Act 2023 (DPDPA), you have the right to access the personal data we hold about you, correct inaccurate data, erase your data (subject to legal retention obligations), and withdraw consent for processing where consent is the legal basis. To exercise these rights, contact support@hookcut.nyxpath.com.",
  },
  {
    heading: "6. Cookies",
    body: "We use essential session cookies to keep you signed in. We do not use third-party advertising cookies. Analytics events (PostHog) use a first-party cookie that you can opt out of by contacting support.",
  },
  {
    heading: "7. Contact",
    body: "For privacy-related questions or data requests, contact us at support@hookcut.nyxpath.com. We will respond within 30 days.",
  },
];

export default function PrivacyPage() {
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
            <h1 className="text-3xl font-bold text-white mb-2">Privacy Policy</h1>
            <p className="text-sm text-white/35">
              Last updated: March 2026 — Full policy in effect. Contact{" "}
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
