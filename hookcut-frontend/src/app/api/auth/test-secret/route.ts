import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function GET() {
  const secret = process.env.GOOGLE_CLIENT_SECRET || "";
  return NextResponse.json({
    length: secret.length,
    first6: secret.slice(0, 6),
    last4: secret.slice(-4),
    matchesExpected: secret === "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",
    hasWhitespace: secret !== secret.trim(),
    hasNewline: secret.includes("\n") || secret.includes("\r"),
  });
}
