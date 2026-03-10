import type { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import CredentialsProvider from "next-auth/providers/credentials";

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
        mode: { label: "Mode", type: "text" },
        name: { label: "Name", type: "text" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        const isRegister = credentials.mode === "register";
        // NEXT_PUBLIC_API_URL already includes /api (e.g. http://localhost:8000/api)
        // NEXTAUTH_BACKEND_URL is the base URL without /api
        const backendUrl =
          process.env.NEXTAUTH_BACKEND_URL ||
          "http://localhost:8000";
        const apiBase = process.env.NEXT_PUBLIC_API_URL || `${backendUrl}/api`;
        const endpoint = isRegister
          ? `${apiBase}/auth/register`
          : `${apiBase}/auth/login`;
        const body: Record<string, string> = {
          email: credentials.email,
          password: credentials.password,
        };
        if (isRegister && credentials.name) {
          body.name = credentials.name;
        }
        try {
          const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          });
          if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data?.detail || "Authentication failed");
          }
          const data = await res.json();
          return {
            id: data.user_id,
            email: data.email,
            name: data.name,
            role: data.role ?? "user",
            accessToken: data.access_token,
          };
        } catch (err) {
          // Propagate the server error message so NextAuth can surface it
          throw err;
        }
      },
    }),
  ],

  // Audit #10 (B1): Session persistence verified — no bug found.
  // SessionProvider wraps all pages in layout.tsx, JWT strategy is correct,
  // cookies are properly configured. The prior symptom (session appearing
  // unauthenticated on navigation) was caused by missing <Header /> on
  // product pages, which was fixed in audit #8.
  session: {
    strategy: "jwt",
  },

  secret: process.env.NEXTAUTH_SECRET,

  debug: true, // TODO: revert to process.env.NODE_ENV === "development" after OAuth fix confirmed

  callbacks: {
    async jwt({ token, user, account }) {
      // On initial sign-in, persist the user id and role into the token
      if (user) {
        token.sub = user.id;
        const userRole = (user as { role?: string }).role;
        if (userRole) {
          // Credentials sign-in — role comes from backend login/register response
          token.role = userRole;
        } else if (account?.provider === "google" && user.email) {
          // Google OAuth sign-in — fetch role from backend since Google doesn't provide it
          const backendUrl =
            process.env.NEXTAUTH_BACKEND_URL || "http://localhost:8000";
          const apiBase =
            process.env.NEXT_PUBLIC_API_URL || `${backendUrl}/api`;
          try {
            const res = await fetch(`${apiBase}/auth/role`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ email: user.email }),
            });
            if (res.ok) {
              const data = await res.json();
              token.role = data.role ?? "user";
            } else {
              token.role = "user";
            }
          } catch {
            token.role = "user";
          }
        } else {
          token.role = "user";
        }
        token.isAdmin = token.role === "admin";
      }
      return token;
    },

    async session({ session, token }) {
      // Expose user id, role, and isAdmin on the client-side session object
      if (session.user) {
        session.user.id = token.sub as string;
        session.user.role = token.role as string | undefined;
        session.user.isAdmin = token.isAdmin as boolean | undefined;
      }
      return session;
    },
  },

  pages: {
    signIn: "/auth/login",
  },
};
