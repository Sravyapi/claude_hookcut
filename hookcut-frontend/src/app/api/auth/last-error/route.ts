import { NextResponse } from "next/server";
import { lastOAuthError } from "../[...nextauth]/route";

export const runtime = "nodejs";

export async function GET() {
  return NextResponse.json({ lastOAuthError });
}
