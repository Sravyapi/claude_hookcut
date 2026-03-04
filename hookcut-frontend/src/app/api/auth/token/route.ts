import { getToken } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";
import * as jose from "jose";

const secret = new TextEncoder().encode(process.env.NEXTAUTH_SECRET!);

export async function GET(req: NextRequest) {
  // Decode NextAuth's JWE token to get the payload
  const decoded = await getToken({ req });
  if (!decoded || !decoded.sub) {
    return NextResponse.json(
      { error: "Not authenticated" },
      { status: 401 },
    );
  }

  // Re-sign as a standard HS256 JWT that the backend can verify
  const token = await new jose.SignJWT({
    sub: decoded.sub,
    email: decoded.email as string,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("1h")
    .sign(secret);

  return NextResponse.json({ token });
}
