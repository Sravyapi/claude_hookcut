/** Detect currency from browser timezone — India → INR, everywhere else → USD */
export function detectCurrency(): "INR" | "USD" {
  if (typeof Intl === "undefined") return "USD";
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return tz?.startsWith("Asia/Kolkata") || tz?.startsWith("Asia/Calcutta")
      ? "INR"
      : "USD";
  } catch {
    return "USD";
  }
}

export function formatPrice(plan: (typeof PLANS)[number], currency: "INR" | "USD"): string {
  const price = currency === "INR" ? plan.priceINR : plan.priceUSD;
  if (price === 0) return "Free";
  const symbol = currency === "INR" ? "₹" : "$";
  return `${symbol}${price}`;
}

export const PLANS = [
  {
    key: "free",
    name: "Free",
    priceUSD: 0,
    priceINR: 0,
    period: null,
    aiMinutes: 120,
    features: [
      "120 AI analysis minutes/month",
      "Unlimited watermarked clips",
      "All 18 hook types",
      "AI scoring (7 dimensions)",
    ],
    cta: "Start Free",
    highlighted: false,
  },
  {
    key: "pro",
    name: "Pro",
    priceUSD: 7,
    priceINR: 499,
    period: "mo",
    aiMinutes: 300,
    features: [
      "300 AI analysis minutes/month",
      "Watermark-free on all clips",
      "Free clips on any analyzed video",
      "All 18 hook types",
      "Priority support",
    ],
    cta: "Go Pro",
    highlighted: true,
  },
] as const;
