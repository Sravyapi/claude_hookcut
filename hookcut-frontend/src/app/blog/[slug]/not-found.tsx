import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#FAFAF8] flex items-center justify-center px-6">
      <div className="max-w-md w-full text-center">
        <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">404</p>
        <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-3">
          Page not found
        </h2>
        <p className="text-[#71717A] text-sm leading-relaxed mb-8">
          This page does not exist or may have been moved.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
        >
          Back to HookCut
        </Link>
      </div>
    </div>
  );
}
