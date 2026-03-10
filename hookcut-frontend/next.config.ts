import type { NextConfig } from "next";
import path from "path";

// Standalone mode + file tracing needed for self-hosted Docker (Railway).
// On Vercel, Vercel handles bundling natively — standalone breaks path resolution.
const isVercel = !!process.env.VERCEL;

const nextConfig: NextConfig = {
  ...(isVercel ? {} : {
    output: "standalone",
    outputFileTracingRoot: path.join(__dirname, "../../"),
  }),
  serverExternalPackages: [],
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Content-Security-Policy-Report-Only",
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: blob:; connect-src 'self' https://api.hookcut.nyxpath.com https://app.posthog.com https://*.sentry.io; frame-src https://accounts.google.com https://www.youtube.com; font-src 'self' data:; object-src 'none'; base-uri 'self';",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
