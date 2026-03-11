import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth";

export const runtime = "nodejs";

// Temporarily store the last OAuth error for debugging
let lastOAuthError: string | null = null;

const handler = NextAuth({
  ...authOptions,
  logger: {
    error(code, metadata) {
      const meta = metadata instanceof Error
        ? metadata.message + " | " + metadata.stack?.split("\n").slice(0, 3).join(" ")
        : JSON.stringify(metadata);
      lastOAuthError = `${code}: ${meta}`;
      console.error("[NextAuth Error]", code, meta);
    },
    warn(code) {
      console.warn("[NextAuth Warn]", code);
    },
    debug(code, metadata) {
      console.debug("[NextAuth Debug]", code, metadata);
    },
  },
});

export { handler as GET, handler as POST };

// Temporary debug endpoint: GET /api/auth/last-error
// This is accessed via the debug route, not this catch-all
export { lastOAuthError };
