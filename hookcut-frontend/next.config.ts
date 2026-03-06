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
        ],
      },
    ];
  },
};

export default nextConfig;
