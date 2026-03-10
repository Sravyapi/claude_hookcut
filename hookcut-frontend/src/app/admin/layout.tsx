"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Users,
  Film,
  BookOpen,
  Cpu,
  ScrollText,
  Shield,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

/* ─── Sidebar navigation items ─── */
const NAV_ITEMS = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/sessions", label: "Sessions", icon: Film },
  { href: "/admin/rules", label: "Rules", icon: BookOpen },
  { href: "/admin/models", label: "Models", icon: Cpu },
  { href: "/admin/audit", label: "Audit Log", icon: ScrollText },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session, status: authStatus } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isAdmin = session?.user?.isAdmin;

  useEffect(() => {
    if (authStatus === "unauthenticated") {
      router.push("/");
    } else if (authStatus === "authenticated" && !isAdmin) {
      router.push("/");
    }
  }, [authStatus, isAdmin, router]);

  /* Close mobile menu on route change */
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  /* ─── Loading state ─── */
  if (authStatus === "loading") {
    return (
      <main className="pt-24 pb-12">
        <div className="max-w-7xl mx-auto px-6 flex gap-6">
          <Skeleton className="w-64 h-[calc(100vh-8rem)] shrink-0 hidden lg:block" />
          <Skeleton className="flex-1 h-[calc(100vh-8rem)]" />
        </div>
      </main>
    );
  }

  /* ─── Gate: not admin ─── */
  if (!session?.user?.isAdmin) {
    return null;
  }

  /* ─── Helper: is link active ─── */
  function isActive(href: string) {
    if (href === "/admin") return pathname === "/admin";
    return pathname.startsWith(href);
  }

  /* ─── Shared nav link renderer ─── */
  function renderNavLink(item: (typeof NAV_ITEMS)[number], mobile?: boolean) {
    const Icon = item.icon;
    const active = isActive(item.href);

    return (
      <Link
        key={item.href}
        href={item.href}
        className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
          active
            ? "text-white bg-[--color-primary]/10 border-l-2 border-[--color-primary]"
            : "text-white/45 hover:text-white/75 hover:bg-white/[0.04] border-l-2 border-transparent"
        } ${mobile ? "" : ""}`}
        title={!mobile && collapsed ? item.label : undefined}
      >
        <Icon
          className={`w-4 h-4 shrink-0 transition-colors ${
            active
              ? "text-[--color-primary]"
              : "text-white/35 group-hover:text-white/55"
          }`}
        />
        {(mobile || !collapsed) && <span className="truncate">{item.label}</span>}
      </Link>
    );
  }

  return (
    <main className="pt-20 pb-12 min-h-screen">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:flex gap-6">
        {/* ─── Mobile top bar ─── */}
        <div className="lg:hidden flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-[--color-primary] shrink-0" />
            <span className="text-sm font-semibold text-white/80">Admin Panel</span>
          </div>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 rounded-xl text-white/50 hover:text-white/70 hover:bg-white/[0.04] transition-colors"
            aria-label={mobileOpen ? "Close admin menu" : "Open admin menu"}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* ─── Mobile drawer ─── */}
        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="lg:hidden overflow-hidden mb-4"
            >
              <nav className="glass-strong rounded-2xl p-3 flex flex-col gap-0.5">
                {NAV_ITEMS.map((item) => renderNavLink(item, true))}
              </nav>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ─── Desktop Sidebar ─── */}
        <motion.aside
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className={`hidden lg:block shrink-0 sticky top-20 self-start h-[calc(100vh-6rem)] transition-all duration-300 ${
            collapsed ? "w-16" : "w-60"
          }`}
        >
          <div className="h-full glass-strong rounded-2xl p-3 flex flex-col">
            {/* Admin badge */}
            <div className="flex items-center gap-2 px-3 py-2.5 mb-2">
              <Shield className="w-4.5 h-4.5 text-[--color-primary] shrink-0" />
              {!collapsed && (
                <span className="text-sm font-semibold text-white/80 truncate">
                  Admin Panel
                </span>
              )}
            </div>

            {/* Divider */}
            <div className="h-px bg-white/[0.06] mb-2" />

            {/* Nav links */}
            <nav className="flex-1 flex flex-col gap-0.5">
              {NAV_ITEMS.map((item) => renderNavLink(item))}
            </nav>

            {/* Collapse toggle */}
            <div className="h-px bg-white/[0.06] mt-2 mb-2" />
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-white/30 hover:text-white/50 hover:bg-white/[0.04] transition-colors text-xs"
            >
              {collapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <>
                  <ChevronLeft className="w-4 h-4" />
                  <span>Collapse</span>
                </>
              )}
            </button>
          </div>
        </motion.aside>

        {/* ─── Content ─── */}
        <div className="flex-1 min-w-0">{children}</div>
      </div>
    </main>
  );
}
