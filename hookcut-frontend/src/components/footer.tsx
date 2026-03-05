import Link from "next/link";

const FOOTER_SECTIONS = [
  {
    heading: "Product",
    links: [
      { href: "/", label: "Analyze" },
      { href: "/dashboard", label: "Dashboard" },
      { href: "/pricing", label: "Pricing" },
      { href: "/settings", label: "Settings" },
    ],
  },
  {
    heading: "Resources",
    links: [
      { href: "/blog", label: "Blog" },
      { href: "/how-it-works", label: "How It Works" },
      { href: "/use-cases/youtube-creators", label: "Use Cases" },
      { href: "/case-studies", label: "Case Studies" },
    ],
  },
  {
    heading: "Compare",
    links: [
      { href: "/opus-clip-alternative", label: "HookCut vs OpusClip" },
      { href: "/klap-alternative", label: "HookCut vs Klap" },
      { href: "/vizard-alternative", label: "HookCut vs Vizard" },
      { href: "/submagic-alternative", label: "HookCut vs Submagic" },
    ],
  },
  {
    heading: "Legal",
    links: [
      { href: "/terms", label: "Terms" },
      { href: "/privacy", label: "Privacy" },
    ],
  },
] as const;

export function Footer() {
  return (
    <footer className="bg-[#0A0A0A] border-t border-white/[0.06]" role="contentinfo">
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2.5 mb-4 group w-fit">
              <div className="w-8 h-8 rounded-lg bg-[--color-primary] flex items-center justify-center">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M14 4C14 4 16 4 16 7C16 10 13 11 10 11C7 11 5 12.5 5 15C5 16.5 6 17.5 7.5 17.5"
                    stroke="white"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M5.5 14L7.5 17.5L4 17.5"
                    stroke="white"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <span className="font-display font-extrabold text-[17px] tracking-tight text-white/80">
                HookCut
              </span>
            </Link>
            <p className="text-sm text-white/35 leading-relaxed max-w-[200px]">
              Find the hook. Stop the scroll.
            </p>
          </div>

          {/* Link columns */}
          {FOOTER_SECTIONS.map((section) => (
            <div key={section.heading}>
              <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-4">
                {section.heading}
              </h3>
              <ul className="flex flex-col gap-2.5">
                {section.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-white/45 hover:text-white/75 transition-colors duration-150"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 pt-6 border-t border-white/[0.05] flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-white/20">
            © 2026 HookCut · Built for creators · ₹499/month
          </p>
          <div className="flex items-center gap-4">
            <Link
              href="/youtube-hook-detector"
              className="text-xs text-white/20 hover:text-white/40 transition-colors"
            >
              YouTube Hook Detector
            </Link>
            <Link
              href="/ai-hook-finder"
              className="text-xs text-white/20 hover:text-white/40 transition-colors"
            >
              AI Hook Finder
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
