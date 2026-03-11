import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth";
import { NextRequest } from "next/server";

export const runtime = "nodejs";

const nextAuth = NextAuth(authOptions);

async function wrappedHandler(req: NextRequest, ctx: { params: Promise<{ nextauth: string[] }> }) {
  try {
    return await nextAuth(req, ctx);
  } catch (error) {
    console.error("[NextAuth] Unhandled error:", error);
    throw error;
  }
}

export { wrappedHandler as GET, wrappedHandler as POST };
