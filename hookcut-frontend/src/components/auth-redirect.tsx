"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

/**
 * Renders nothing. Redirects authenticated users to /dashboard.
 * Drop into server-component pages that should not be visible to logged-in users.
 */
export default function AuthRedirect() {
  const { status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "authenticated") router.push("/dashboard");
  }, [status, router]);

  return null;
}
