"use client";

import { createContext, useContext, useEffect, useRef, useState } from "react";
import { SessionProvider, useSession } from "next-auth/react";
import { api } from "@/lib/api";

interface UserContextValue {
  role: string | null;
}

const UserContext = createContext<UserContextValue>({ role: null });

export function useUser() {
  return useContext(UserContext);
}

function AuthSync({ setRole }: { setRole: (role: string) => void }) {
  const { data: session, status } = useSession();
  const synced = useRef(false);

  useEffect(() => {
    if (status === "authenticated" && session?.user?.email && !synced.current) {
      synced.current = true;
      api
        .syncUser(session.user.email)
        .then((data) => {
          if (data.role) setRole(data.role);
        })
        .catch(() => {
          synced.current = false;
        });
    }
  }, [status, session?.user?.email, setRole]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<string | null>(null);

  return (
    <SessionProvider>
      <UserContext.Provider value={{ role }}>
        <AuthSync setRole={setRole} />
        {children}
      </UserContext.Provider>
    </SessionProvider>
  );
}
