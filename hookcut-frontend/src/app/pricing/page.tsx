"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, Zap, Sparkles, Crown, ChevronDown } from "lucide-react";
import { api } from "@/lib/api";
import type { PlansResponse, PlanInfo } from "@/lib/types";
import { PAYG_OPTIONS } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { staggerContainer, fadeUpItem } from "@/lib/motion";

/* ─── Constants ─── */
const TIER_ICONS: Record<string, React.ReactNode> = {
  free: <Sparkles className="w-5 h-5" />,
  lite: <Zap className="w-5 h-5" />,
  pro: <Crown className="w-5 h-5" />,
};

const TIER_FEATURES: Record<string, string[]> = {
  free: ["5 analysis minutes", "Watermarked output", "All 18 hook types", "Community support"],
  lite: ["60 watermark-free minutes", "No watermarks", "Hook regeneration", "Priority processing"],
  pro: ["300 watermark-free minutes", "No watermarks", "Advanced analytics", "Priority support", "Hook regeneration"],
};

const TIER_STYLES: Record<
  string,
  { topBorder: string; badge?: string; glow: string; recommended?: boolean }
> = {
  free: {
    topBorder: "from-white/[0.06] to-white/[0.02]",
    glow: "",
  },
  lite: {
    topBorder: "from-violet-500 to-purple-600",
    badge: "Most Popular",
    glow: "shadow-[0_0_40px_rgba(139,92,246,0.12)]",
    recommended: true,
  },
  pro: {
    topBorder: "from-purple-400 via-violet-500 to-indigo-600",
    glow: "shadow-[0_0_50px_rgba(139,92,246,0.16)]",
  },
};

/* ─── Feature comparison data ─── */
const COMPARISON_FEATURES = [
  { label: "Minutes / month", free: "5 min", lite: "60 min", pro: "300 min" },
  { label: "Watermark-free output", free: false, lite: true, pro: true },
  { label: "All 18 hook types", free: true, lite: true, pro: true },
  { label: "AI scoring (7 dimensions)", free: true, lite: true, pro: true },
  { label: "Hook regeneration", free: false, lite: true, pro: true },
  { label: "Priority processing", free: false, lite: true, pro: true },
  { label: "Advanced analytics", free: false, lite: false, pro: true },
  { label: "Priority support", free: false, lite: false, pro: true },
];

/* ─── FAQ data ─── */
const FAQS = [
  {
    q: "How are minutes counted?",
    a: "Minutes are based on the duration of the source YouTube video you analyze. A 10-minute video costs 10 minutes from your balance.",
  },
  {
    q: "Do credits expire?",
    a: "Subscription credits reset at the start of each billing month. Pay-As-You-Go credits never expire and roll over indefinitely.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Yes. Canceling stops renewal at the end of the current billing period. You keep access until the period ends.",
  },
  {
    q: "What format are the Shorts in?",
    a: "MP4 with H.264 video and AAC audio, 1080×1920 (9:16), with burned-in captions and optional watermark.",
  },
  {
    q: "What YouTube video length is supported?",
    a: "Videos up to 60 minutes long are supported. Longer videos may be added in a future update.",
  },
];

/* ─── Sub-components ─── */

function FeatureCell({ value }: { value: string | boolean }) {
  if (typeof value === "boolean") {
    return value ? (
      <Check className="w-4 h-4 text-emerald-400 mx-auto" />
    ) : (
      <X className="w-4 h-4 text-white/15 mx-auto" />
    );
  }
  return <span className="text-xs text-white/60 font-medium">{value}</span>;
}

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-white/[0.05] last:border-0">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full flex items-center justify-between py-4 text-left"
      >
        <span className="text-sm font-medium text-white/75">{q}</span>
        <ChevronDown
          className={`w-4 h-4 text-white/30 shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <p className="text-sm text-white/45 leading-relaxed pb-4">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Main page ─── */
export default function PricingPage() {
  const { status: authStatus } = useSession();
  const router = useRouter();

  const [plans, setPlans] = useState<PlansResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [paygIdx, setPaygIdx] = useState(0);
  const [paygLoading, setPaygLoading] = useState(false);
  const [comparisonOpen, setComparisonOpen] = useState(false);

  const paygMinutes = PAYG_OPTIONS[paygIdx];

  useEffect(() => {
    setLoading(true);
    api
      .getPlans()
      .then(setPlans)
      .catch((err) => console.warn("Failed to load plans:", err))
      .finally(() => setLoading(false));
  }, []);

  const handleUpgrade = async (tier: string) => {
    if (authStatus !== "authenticated") {
      router.push("/auth/login");
      return;
    }
    setCheckoutLoading(tier);
    try {
      const result = await api.createCheckout(tier);
      if (result?.checkout_url) window.location.href = result.checkout_url;
    } catch (err) {
      console.warn("Checkout failed:", err);
    } finally {
      setCheckoutLoading(null);
    }
  };

  const handlePaygPurchase = async () => {
    if (authStatus !== "authenticated") {
      router.push("/auth/login");
      return;
    }
    setPaygLoading(true);
    try {
      await api.purchasePayg(paygMinutes);
      router.push("/dashboard");
    } catch (err) {
      console.warn("PAYG purchase failed:", err);
    } finally {
      setPaygLoading(false);
    }
  };

  const currency = plans?.currency || "USD";
  const currentTier = plans?.current_tier || "free";

  const formatPrice = (plan: PlanInfo) => {
    if (plan.tier === "free") return "Free";
    return plan.price_display;
  };

  /* Static fallback plans */
  const staticPlans = [
    {
      tier: "free",
      name: "Free",
      price: "Free",
      desc: "5 min included",
      features: ["5 analysis minutes", "Watermarked output", "All 18 hook types", "Community support"],
    },
    {
      tier: "lite",
      name: "Lite",
      price: "$9",
      desc: "60 watermark-free min",
      features: ["60 watermark-free minutes", "No watermarks", "Hook regeneration", "Priority processing"],
    },
    {
      tier: "pro",
      name: "Pro",
      price: "$29",
      desc: "300 watermark-free min",
      features: ["300 watermark-free minutes", "No watermarks", "Advanced analytics", "Priority support", "Hook regeneration"],
    },
  ];

  return (
    <main className="pt-24 pb-16">
      <div className="max-w-5xl mx-auto px-6">
        {/* Page header */}
        <motion.div
          className="text-center mb-14"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-violet-500/8 border border-violet-500/15 text-violet-300 text-xs font-medium mb-5">
            <Sparkles className="w-3.5 h-3.5" />
            Simple, transparent pricing
          </div>
          <h1 className="text-4xl font-bold text-white mb-3">
            Choose Your <span className="gradient-text">Plan</span>
          </h1>
          <p className="text-white/45 max-w-md mx-auto text-sm">
            Unlock more minutes, remove watermarks, and supercharge your Shorts production.
          </p>
        </motion.div>

        {/* Plan cards */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-12">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-96" />
            ))}
          </div>
        ) : (
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-12 items-start"
            variants={staggerContainer}
            initial="hidden"
            animate="show"
          >
            {(plans?.plans ?? staticPlans).map((plan) => {
              const styles = TIER_STYLES[plan.tier] || TIER_STYLES.free;
              const isCurrent = plan.tier === currentTier;
              const isRecommended = styles.recommended;

              const price = plans
                ? formatPrice(plan as PlanInfo)
                : (plan as (typeof staticPlans)[number]).price;
              const desc = plans
                ? (plan as PlanInfo).watermark_free_minutes > 0
                  ? `${(plan as PlanInfo).watermark_free_minutes} watermark-free min`
                  : "Watermarked output"
                : (plan as (typeof staticPlans)[number]).desc;
              const features = TIER_FEATURES[plan.tier] ?? (plan as (typeof staticPlans)[number]).features;

              return (
                <motion.div
                  key={plan.tier}
                  variants={fadeUpItem}
                  className={`relative glass rounded-2xl overflow-hidden flex flex-col transition-all duration-300 ${styles.glow} ${
                    isRecommended
                      ? "md:-mt-2 md:mb-2 ring-2 ring-violet-500/30"
                      : "hover:border-white/10"
                  } ${isCurrent ? "ring-2 ring-violet-500/50" : ""}`}
                  whileHover={{ y: isRecommended ? -4 : -2 }}
                  transition={{ type: "spring", stiffness: 300, damping: 25 }}
                >
                  {/* Gradient top border */}
                  <div
                    className={`h-[3px] bg-gradient-to-r ${styles.topBorder}`}
                  />

                  {/* Badge */}
                  {(styles.badge || isCurrent) && (
                    <div className="absolute top-3 right-3">
                      <span
                        className={`text-[10px] px-2.5 py-1 rounded-full font-semibold ${
                          isCurrent
                            ? "bg-violet-500/20 text-violet-200 border border-violet-500/30"
                            : "bg-violet-500 text-white"
                        }`}
                      >
                        {isCurrent ? "Current Plan" : styles.badge}
                      </span>
                    </div>
                  )}

                  <div className="p-6 flex flex-col flex-1">
                    {/* Tier info */}
                    <div className="flex items-center gap-2.5 mb-4">
                      <div
                        className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                          plan.tier === "pro"
                            ? "bg-purple-500/15 text-purple-300"
                            : plan.tier === "lite"
                              ? "bg-violet-500/15 text-violet-300"
                              : "bg-white/[0.06] text-white/50"
                        }`}
                      >
                        {TIER_ICONS[plan.tier]}
                      </div>
                      <h3 className="text-lg font-bold text-white">
                        {plans ? plan.tier.charAt(0).toUpperCase() + plan.tier.slice(1) : (plan as (typeof staticPlans)[number]).name}
                      </h3>
                    </div>

                    <div className="flex items-baseline gap-1.5 mb-1">
                      <span className="text-4xl font-bold text-white">{price}</span>
                      {plan.tier !== "free" && (
                        <span className="text-sm text-white/35">/month</span>
                      )}
                    </div>
                    <p className="text-xs text-white/40 mb-6">{desc}</p>

                    {/* Features */}
                    <ul className="space-y-2.5 flex-1 mb-6">
                      {features.map((feature, i) => (
                        <li key={i} className="flex items-start gap-2.5">
                          <Check className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
                          <span className="text-sm text-white/65">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    {/* CTA */}
                    {isCurrent ? (
                      <button className="btn-secondary w-full text-sm" disabled>
                        Current Plan
                      </button>
                    ) : plan.tier === "free" ? (
                      <button className="btn-secondary w-full text-sm opacity-50" disabled>
                        Free Tier
                      </button>
                    ) : (
                      <button
                        className="btn-primary w-full text-sm"
                        onClick={() => handleUpgrade(plan.tier)}
                        disabled={checkoutLoading === plan.tier}
                      >
                        {checkoutLoading === plan.tier
                          ? "Redirecting..."
                          : `Upgrade to ${plans ? plan.tier.charAt(0).toUpperCase() + plan.tier.slice(1) : (plan as (typeof staticPlans)[number]).name}`}
                      </button>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}

        {/* Feature comparison toggle */}
        <motion.div
          className="mb-12"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <button
            onClick={() => setComparisonOpen(!comparisonOpen)}
            className="flex items-center gap-2 mx-auto text-sm text-white/40 hover:text-white/60 transition-colors"
          >
            <span>Compare all features</span>
            <ChevronDown
              className={`w-4 h-4 transition-transform duration-200 ${comparisonOpen ? "rotate-180" : ""}`}
            />
          </button>

          <AnimatePresence>
            {comparisonOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className="glass-card rounded-2xl overflow-hidden mt-6">
                  {/* Table header */}
                  <div className="grid grid-cols-4 gap-4 px-6 py-3 border-b border-white/[0.06] bg-white/[0.02]">
                    <span className="text-xs text-white/30 font-medium">Feature</span>
                    {["Free", "Lite", "Pro"].map((t) => (
                      <span
                        key={t}
                        className="text-xs font-semibold text-center text-white/60"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                  {COMPARISON_FEATURES.map((row, i) => (
                    <div
                      key={i}
                      className={`grid grid-cols-4 gap-4 px-6 py-3 items-center ${
                        i % 2 === 0 ? "" : "bg-white/[0.01]"
                      } border-b border-white/[0.04] last:border-0`}
                    >
                      <span className="text-xs text-white/50">{row.label}</span>
                      <div className="text-center">
                        <FeatureCell value={row.free} />
                      </div>
                      <div className="text-center">
                        <FeatureCell value={row.lite} />
                      </div>
                      <div className="text-center">
                        <FeatureCell value={row.pro} />
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* PAYG section */}
        <motion.div
          className="glass-card rounded-2xl p-8 max-w-2xl mx-auto mb-12"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="text-center mb-6">
            <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center mx-auto mb-3">
              <Zap className="w-5 h-5 text-violet-400" />
            </div>
            <h2 className="text-lg font-bold text-white mb-1">Need More Minutes?</h2>
            <p className="text-white/40 text-sm">
              Top up anytime. No subscription required. Credits never expire.
            </p>
          </div>

          {/* Slider */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-white/30">Minutes</span>
              <motion.span
                key={paygMinutes}
                initial={{ scale: 0.9, opacity: 0.5 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-xl font-bold gradient-text tabular-nums"
              >
                {paygMinutes} min
              </motion.span>
            </div>
            <input
              type="range"
              min={0}
              max={3}
              step={1}
              value={paygIdx}
              onChange={(e) => setPaygIdx(Number(e.target.value))}
              className="w-full h-1.5 rounded-full appearance-none bg-white/10 cursor-pointer accent-violet-500"
              style={{
                background: `linear-gradient(to right, #8b5cf6 0%, #8b5cf6 ${(paygIdx / 3) * 100}%, rgba(255,255,255,0.1) ${(paygIdx / 3) * 100}%, rgba(255,255,255,0.1) 100%)`,
              }}
            />
            <div className="flex justify-between mt-2">
              {PAYG_OPTIONS.map((m) => (
                <span key={m} className="text-[10px] text-white/25">
                  {m}
                </span>
              ))}
            </div>
          </div>

          <button
            onClick={handlePaygPurchase}
            disabled={paygLoading}
            className="btn-primary w-full text-sm"
          >
            {paygLoading ? "Processing..." : `Purchase ${paygMinutes} Minutes`}
          </button>
        </motion.div>

        {/* FAQ */}
        <motion.div
          className="max-w-2xl mx-auto"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <h2 className="text-lg font-bold text-white/80 mb-4 text-center">
            Frequently Asked Questions
          </h2>
          <div className="glass-card rounded-2xl px-6">
            {FAQS.map((faq, i) => (
              <FaqItem key={i} q={faq.q} a={faq.a} />
            ))}
          </div>
        </motion.div>
      </div>
    </main>
  );
}
