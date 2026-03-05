"use client";
import Link from "next/link";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  return (
    <div className="min-h-screen bg-[#FAFAF8] flex items-center justify-center px-6">
      <div className="max-w-md w-full text-center">
        <p className="text-[#E84A2F] text-xs font-semibold uppercase tracking-widest mb-3">Error</p>
        <h2 className="text-2xl font-[family-name:--font-display] font-bold text-[#0A0A0A] mb-3">
          Something went wrong
        </h2>
        <p className="text-[#71717A] text-sm leading-relaxed mb-8">
          {error.message || "An unexpected error occurred. Please try again."}
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-5 py-2.5 rounded-lg bg-[#E84A2F] text-white text-sm font-semibold hover:bg-[#D13F25] transition-colors"
          >
            Try again
          </button>
          <Link
            href="/"
            className="px-5 py-2.5 rounded-lg border border-[#E4E4E7] text-[#0A0A0A] text-sm font-semibold hover:bg-[#F4F4F5] transition-colors"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}
