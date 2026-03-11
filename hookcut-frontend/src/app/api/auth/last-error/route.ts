import { NextResponse } from "next/server";

export const runtime = "nodejs";

// Store last error in module scope (persists within same serverless invocation)
let lastError: string | null = null;

export function setLastError(err: string) {
  lastError = err;
}

export async function GET() {
  return NextResponse.json({ lastError });
}
