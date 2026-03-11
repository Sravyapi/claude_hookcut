import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth";
import { setLastError } from "../last-error/route";

export const runtime = "nodejs";

const handler = NextAuth({
  ...authOptions,
  logger: {
    error(code, metadata) {
      const meta = metadata instanceof Error
        ? metadata.message
        : JSON.stringify(metadata);
      setLastError(`${code}: ${meta}`);
    },
    warn(code) { /* noop */ },
    debug(code, metadata) { /* noop */ },
  },
});

export { handler as GET, handler as POST };
