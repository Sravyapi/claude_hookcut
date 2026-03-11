import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    GOOGLE_CLIENT_ID_set: !!process.env.GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_ID_length: process.env.GOOGLE_CLIENT_ID?.length ?? 0,
    GOOGLE_CLIENT_ID_preview: process.env.GOOGLE_CLIENT_ID?.slice(0, 10) ?? "MISSING",
    GOOGLE_CLIENT_SECRET_set: !!process.env.GOOGLE_CLIENT_SECRET,
    GOOGLE_CLIENT_SECRET_length: process.env.GOOGLE_CLIENT_SECRET?.length ?? 0,
    NEXTAUTH_SECRET_set: !!process.env.NEXTAUTH_SECRET,
    NEXTAUTH_URL: process.env.NEXTAUTH_URL ?? "MISSING",
    NEXTAUTH_BACKEND_URL: process.env.NEXTAUTH_BACKEND_URL ?? "MISSING",
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "MISSING",
    NODE_ENV: process.env.NODE_ENV,
  });
}
