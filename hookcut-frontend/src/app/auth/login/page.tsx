"use client";

import { useState, useEffect } from "react";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

const TESTIMONIALS = [
  {
    quote: "Generated 50 Shorts from one podcast. Insane ROI.",
    author: "Alex M.",
    role: "Content Creator",
  },
  {
    quote: "Hook quality is 10x better than manual editing. I'm hooked.",
    author: "Sarah K.",
    role: "YouTube Producer",
  },
  {
    quote: "Cut my Short creation time from 2 hours to 10 minutes.",
    author: "James T.",
    role: "Indie Creator",
  },
];

/* Google's official colored "G" mark */
function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  );
}

export default function LoginPage() {
  const [testimonialIdx, setTestimonialIdx] = useState(0);

  useEffect(() => {
    const t = setInterval(
      () => setTestimonialIdx((i) => (i + 1) % TESTIMONIALS.length),
      4000
    );
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16">
      {/* Background orbs — more dramatic */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/3 left-1/4 w-[600px] h-[600px] rounded-full bg-violet-600/[0.08] blur-[140px] float-slow" />
        <div className="absolute bottom-1/3 right-1/4 w-[500px] h-[500px] rounded-full bg-purple-600/[0.06] blur-[120px] float-slower" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] rounded-full bg-indigo-500/[0.04] blur-[80px]" />
      </div>

      <motion.div
        className="relative w-full max-w-sm"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 180, damping: 22 }}
      >
        {/* Card */}
        <div className="glass-strong rounded-3xl p-8">
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center text-white font-bold text-2xl shadow-xl shadow-violet-500/30">
              H
            </div>
          </div>

          {/* Heading */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-white mb-2">
              Sign in to <span className="gradient-text">HookCut</span>
            </h1>
            <p className="text-white/40 text-sm leading-relaxed">
              Turn YouTube videos into viral Shorts with AI-powered hook
              detection
            </p>
          </div>

          {/* Google button */}
          <button
            onClick={() => signIn("google", { callbackUrl: "/" })}
            className="w-full flex items-center justify-center gap-3 px-5 py-3.5 rounded-xl bg-white text-gray-800 font-semibold text-sm hover:bg-gray-50 transition-colors duration-200 shadow-lg shadow-black/20 mb-5"
          >
            <GoogleIcon className="w-5 h-5" />
            Continue with Google
          </button>

          {/* Trust text */}
          <div className="flex items-center justify-center gap-2 text-xs text-white/25 mb-6">
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            No credit card required · 5 free minutes included
          </div>

          {/* Legal */}
          <p className="text-center text-[11px] text-white/20 leading-relaxed mb-4">
            By signing in, you agree to our{" "}
            <span className="text-white/35 hover:text-white/50 cursor-pointer transition-colors">
              Terms of Service
            </span>{" "}
            and{" "}
            <span className="text-white/35 hover:text-white/50 cursor-pointer transition-colors">
              Privacy Policy
            </span>
            .
          </p>

          <div className="text-center">
            <Link
              href="/"
              className="text-sm text-violet-400/70 hover:text-violet-300 transition-colors"
            >
              ← Back to home
            </Link>
          </div>
        </div>

        {/* Rotating testimonial */}
        <div className="mt-6 px-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={testimonialIdx}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.3 }}
              className="text-center"
            >
              <p className="text-xs text-white/30 italic leading-relaxed mb-2">
                &ldquo;{TESTIMONIALS[testimonialIdx].quote}&rdquo;
              </p>
              <div className="flex items-center justify-center gap-1.5">
                <span className="text-[11px] font-medium text-white/40">
                  {TESTIMONIALS[testimonialIdx].author}
                </span>
                <span className="text-[11px] text-white/20">·</span>
                <span className="text-[11px] text-white/25">
                  {TESTIMONIALS[testimonialIdx].role}
                </span>
              </div>
            </motion.div>
          </AnimatePresence>
          {/* Dots */}
          <div className="flex items-center justify-center gap-1.5 mt-3">
            {TESTIMONIALS.map((_, i) => (
              <button
                key={i}
                onClick={() => setTestimonialIdx(i)}
                className={`w-1.5 h-1.5 rounded-full transition-all duration-200 ${
                  i === testimonialIdx ? "bg-violet-400 w-3" : "bg-white/15"
                }`}
              />
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
