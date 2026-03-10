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
    minutes: 120,
    features: ["5 hooks per video", "3 Shorts per video", "Watermarked"],
    cta: "Start Free",
    highlighted: false,
  },
  {
    key: "lite",
    name: "Lite",
    priceUSD: 7,
    priceINR: 499,
    period: "mo",
    minutes: 100,
    minutesLabel: "100 watermark-free minutes",
    features: ["5 hooks per video", "3 Shorts per video", "100 watermark-free minutes", "Priority support"],
    cta: "Go Lite",
    highlighted: true,
  },
  {
    key: "pro",
    name: "Pro",
    priceUSD: 13,
    priceINR: 999,
    period: "mo",
    minutes: 500,
    minutesLabel: "500 watermark-free minutes",
    features: ["5 hooks per video", "Unlimited Shorts", "500 watermark-free minutes", "Priority support", "Early access"],
    cta: "Go Pro",
    highlighted: false,
  },
] as const;
