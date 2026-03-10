import Link from "next/link";
import { Twitter, Youtube, Linkedin } from "lucide-react";

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
      { href: "/blog", label: "Blog & Case Studies" },
      { href: "/how-it-works", label: "How It Works" },
      { href: "/use-cases/youtube-creators", label: "Use Cases" },
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
      <div className="max-w-6xl mx-auto px-6 py-16 pb-20 sm:pb-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center mb-4 group w-fit">
              <span className="font-display font-extrabold text-[22px] tracking-tight leading-none select-none" aria-label="HookCut">
                <span className="text-white/90">Hook</span>
                <span className="relative inline-block text-[#E84A2F]">
                  <svg
                    aria-hidden="true"
                    className="absolute pointer-events-none"
                    style={{ top: -10, left: 1 }}
                    width="14"
                    height="8"
                    viewBox="0 0 14 8"
                    fill="none"
                  >
                    <path
                      d="M 1 7 C 3.5 0.5 10.5 0.5 13 7"
                      stroke="#E84A2F"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                    />
                  </svg>
                  Cut
                </span>
              </span>
            </Link>
            <p className="text-sm text-white/35 leading-relaxed max-w-[240px]">
              Turn any YouTube video into a scroll-stopping Short. AI-powered. Creator-first.
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

        {/* Social links */}
        <div className="mt-12 flex items-center gap-4">
          <a href="#" aria-disabled="true" title="Coming soon" aria-label="Follow us on Twitter" className="text-white/25 cursor-default pointer-events-none transition-colors duration-150" rel="noopener noreferrer" target="_blank">
            <Twitter className="w-4 h-4" aria-hidden="true" />
          </a>
          <a href="#" aria-disabled="true" title="Coming soon" aria-label="Follow us on YouTube" className="text-white/25 cursor-default pointer-events-none transition-colors duration-150" rel="noopener noreferrer" target="_blank">
            <Youtube className="w-4 h-4" aria-hidden="true" />
          </a>
          <a href="#" aria-disabled="true" title="Coming soon" aria-label="Follow us on LinkedIn" className="text-white/25 cursor-default pointer-events-none transition-colors duration-150" rel="noopener noreferrer" target="_blank">
            <Linkedin className="w-4 h-4" aria-hidden="true" />
          </a>
        </div>

        {/* Gradient rule */}
        <div className="mt-10 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

        <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-white/20">
            © 2026 HookCut · Built for creators · Made in India
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
