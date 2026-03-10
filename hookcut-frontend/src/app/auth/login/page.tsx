"use client";

import { useState, useEffect } from "react";
import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

const claims = [
  { text: "No subscription required — pay only for what you use", icon: "💳", label: "Flexible Pricing" },
  { text: "120 minutes free with every account — no credit card needed", icon: "🎁", label: "Free to Try" },
  { text: "AI identifies hooks across 18 hook types and 6 funnel roles", icon: "🤖", label: "AI-Powered" },
  { text: "Generate YouTube Shorts in under 2 minutes", icon: "⚡", label: "Lightning Fast" },
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

const AUTH_ERRORS: Record<string, string> = {
  Callback: "Sign-in failed during callback. Try again.",
  OAuthCallback: "OAuth callback error. Check your Google account settings.",
  OAuthCreateAccount: "Could not create account. Contact support.",
  OAuthAccountNotLinked: "This email is already linked to another account.",
  SessionRequired: "You must be signed in to access that page.",
  CredentialsSignin: "Invalid email or password.",
  Default: "An unexpected error occurred. Please try again.",
};

export default function LoginPage() {
  const [claimIdx, setClaimIdx] = useState(0);
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const callbackUrl = searchParams.get("callbackUrl") || "/";

  // Email/password form state
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [emailError, setEmailError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const t = setInterval(
      () => setClaimIdx((i) => (i + 1) % claims.length),
      4000
    );
    return () => clearInterval(t);
  }, []);

  function handleModeToggle() {
    setAuthMode((m) => (m === "login" ? "signup" : "login"));
    setEmailError("");
  }

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault();
    setEmailError("");
    setIsSubmitting(true);

    try {
      const result = await signIn("credentials", {
        redirect: false,
        email,
        password,
        mode: authMode === "signup" ? "register" : "login",
        name: authMode === "signup" ? name : "",
        callbackUrl,
      });

      if (result?.error) {
        // NextAuth surfaces CredentialsSignin or the thrown error message
        const msg =
          result.error === "CredentialsSignin"
            ? AUTH_ERRORS.CredentialsSignin
            : result.error;
        setEmailError(msg);
      } else if (result?.ok) {
        window.location.href = callbackUrl;
      }
    } catch {
      setEmailError("Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16">
      {/* Background orbs — more dramatic */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/3 left-1/4 w-[600px] h-[600px] rounded-full bg-[var(--color-primary)]/[0.08] blur-[140px] float-slow" />
        <div className="absolute bottom-1/3 right-1/4 w-[500px] h-[500px] rounded-full bg-[var(--color-primary)]/[0.06] blur-[120px] float-slower" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] rounded-full bg-[var(--color-primary)]/[0.04] blur-[80px]" />
      </div>

      <motion.div
        className="relative w-full max-w-sm"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 180, damping: 22 }}
      >
        {/* Card */}
        <div className="glass-strong rounded-3xl p-6 min-[380px]:p-8 shadow-[var(--shadow-modal)]">
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 rounded-2xl bg-[var(--color-primary)] flex items-center justify-center shadow-xl shadow-[var(--color-primary)]/30">
              <span className="gradient-text font-bold text-3xl">H</span>
            </div>
          </div>

          {/* Heading */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-white mb-2">
              {authMode === "login" ? "Sign in to" : "Join"}{" "}
              <span className="text-[var(--color-primary)]">HookCut</span>
            </h1>
            <p className="text-white/40 text-sm leading-relaxed">
              Turn YouTube videos into viral Shorts with AI-powered hook
              detection
            </p>
          </div>

          {/* Error banner (OAuth / URL errors) */}
          {error && (
            <div className="mb-5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
              {AUTH_ERRORS[error] ?? AUTH_ERRORS.Default}
              <span className="block text-xs text-red-400/60 mt-0.5">Error: {error}</span>
            </div>
          )}

          {/* Google button */}
          <button
            onClick={() => signIn("google", { callbackUrl })}
            className="w-full flex items-center justify-center gap-3 px-5 py-3.5 min-h-[48px] rounded-xl bg-white text-gray-800 font-semibold text-sm hover:bg-gray-50 transition-colors duration-200 shadow-lg shadow-black/20"
          >
            <GoogleIcon className="w-5 h-5" />
            Continue with Google
          </button>

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-xs text-white/25 font-medium">or</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          {/* Email/password form */}
          <form onSubmit={handleEmailSubmit} noValidate>
            {authMode === "signup" && (
              <div className="mb-3">
                <label
                  htmlFor="name"
                  className="block text-xs text-white/50 mb-1.5 font-medium"
                >
                  Full name
                </label>
                <input
                  id="name"
                  type="text"
                  autoComplete="name"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/20 focus:outline-none focus:border-[var(--color-primary)]/50 focus:bg-white/8 transition-colors"
                />
              </div>
            )}

            <div className="mb-3">
              <label
                htmlFor="email"
                className="block text-xs text-white/50 mb-1.5 font-medium"
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/20 focus:outline-none focus:border-[var(--color-primary)]/50 focus:bg-white/8 transition-colors"
              />
            </div>

            <div className="mb-4">
              <label
                htmlFor="password"
                className="block text-xs text-white/50 mb-1.5 font-medium"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete={authMode === "signup" ? "new-password" : "current-password"}
                required
                minLength={authMode === "signup" ? 8 : 1}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={authMode === "signup" ? "At least 8 characters" : "Your password"}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/20 focus:outline-none focus:border-[var(--color-primary)]/50 focus:bg-white/8 transition-colors"
              />
            </div>

            {/* Inline error */}
            {emailError && (
              <div className="mb-4 px-3.5 py-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                {emailError}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full px-5 py-3 rounded-xl bg-[var(--color-primary)] text-white font-semibold text-sm hover:bg-[var(--color-primary)]/90 transition-colors duration-200 disabled:opacity-60 disabled:cursor-not-allowed shadow-lg shadow-[var(--color-primary)]/20"
            >
              {isSubmitting
                ? authMode === "signup"
                  ? "Creating account..."
                  : "Signing in..."
                : authMode === "signup"
                ? "Create account"
                : "Sign in"}
            </button>
          </form>

          {/* Mode toggle */}
          <p className="text-center text-xs text-white/30 mt-4">
            {authMode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
            <button
              type="button"
              onClick={handleModeToggle}
              className="text-[var(--color-primary)]/80 hover:text-[var(--color-primary)] transition-colors font-medium"
            >
              {authMode === "login" ? "Sign up" : "Sign in"}
            </button>
          </p>

          {/* Trust text */}
          <div className="flex items-center justify-center gap-2 text-xs text-white/25 mt-5 mb-4">
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
            120 minutes free · No credit card
          </div>

          {/* Legal */}
          <p className="text-center text-[11px] text-white/20 leading-relaxed mb-4">
            By signing in, you agree to our{" "}
            <Link href="/terms" className="underline hover:text-white transition-colors">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/privacy" className="underline hover:text-white transition-colors">
              Privacy Policy
            </Link>
            .
          </p>

        </div>

        {/* Back to home */}
        <div className="text-center mt-4">
          <Link
            href="/"
            className="text-sm text-[var(--color-primary)]/70 hover:text-[var(--color-primary)] transition-colors"
          >
            ← Back to home
          </Link>
        </div>

        {/* Rotating product claims */}
        <div className="mt-6 px-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={claimIdx}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.3 }}
              className="text-center"
            >
              <span className="inline-block text-[10px] px-2.5 py-1 rounded-full bg-[var(--color-primary)]/15 text-[var(--color-primary)]/80 border border-[var(--color-primary)]/20 font-medium mb-2">
                {claims[claimIdx].label}
              </span>
              <p className="text-xs text-white/50 leading-relaxed">
                {claims[claimIdx].icon} {claims[claimIdx].text}
              </p>
            </motion.div>
          </AnimatePresence>
          {/* Dots */}
          <div className="flex items-center justify-center gap-1.5 mt-3">
            {claims.map((_, i) => (
              <button
                key={i}
                onClick={() => setClaimIdx(i)}
                aria-label={`View claim ${i + 1}`}
                className={`w-2 h-2 rounded-full transition-all duration-200 ${
                  i === claimIdx ? "bg-[var(--color-primary)] w-4" : "bg-white/15"
                }`}
              />
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
