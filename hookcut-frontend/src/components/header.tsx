"use client";

import { useCallback, useEffect, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { LogOut, LayoutDashboard, Settings, CreditCard, Menu, X } from "lucide-react";
import { api } from "@/lib/api";
import { useUser } from "@/components/providers";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";

const NAV_LINKS = [
  { href: "/#features", label: "Features", match: "features" },
  { href: "/#pricing", label: "Pricing", match: "pricing" },
  { href: "/use-cases", label: "Use Cases", match: "use-cases" },
  { href: "/blog", label: "Blog", match: "blog" },
] as const;

interface HeaderProps {
  onReset?: () => void;
}

function HookCutWordmark() {
  return (
    <span
      className="font-display font-extrabold text-[18px] tracking-tight leading-none select-none"
      aria-label="HookCut"
    >
      <span className="text-white/90">Hook</span>
      <span className="relative inline-block text-[#E84A2F]">
        {/* Curved hook accent above the C */}
        <svg
          aria-hidden="true"
          className="absolute pointer-events-none"
          style={{ top: -8, left: 1 }}
          width="12"
          height="7"
          viewBox="0 0 12 7"
          fill="none"
        >
          <path
            d="M 1 6 C 3 0.5 9 0.5 11 6"
            stroke="#E84A2F"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
        Cut
      </span>
    </span>
  );
}


export default function Header({ onReset }: HeaderProps) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const { role } = useUser();
  const [balance, setBalance] = useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isAdmin = role === "admin";

  const { scrollY } = useScroll();
  const headerBgOpacity = useTransform(scrollY, [0, 80], [0, 1]);
  const headerBorderOpacity = useTransform(scrollY, [0, 80], [0, 1]);
  const bgColor = useTransform(
    headerBgOpacity,
    (v) => `rgba(17, 17, 17, ${0.5 + v * 0.45})`
  );
  const bgFilter = useTransform(
    headerBgOpacity,
    (v) => `blur(${16 + v * 16}px) saturate(${1 + v * 0.3})`
  );
  const borderColor = useTransform(
    headerBorderOpacity,
    (v) => `rgba(255, 255, 255, ${v * 0.06})`
  );

  useEffect(() => {
    if (status !== "authenticated") return;
    api.getBalance().then((b) => setBalance(b.total_available)).catch(() => undefined);
  }, [status]);

  const userInitials = session?.user?.name
    ? session.user.name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : session?.user?.email
      ? session.user.email[0].toUpperCase()
      : "U";

  const handleLogoClick = useCallback(() => {
    if (onReset) {
      onReset();
    } else {
      router.push("/");
    }
  }, [onReset, router]);

  const handleSignOut = useCallback(() => {
    signOut({ callbackUrl: "/" });
  }, []);

  const closeMobileMenu = useCallback(() => setMobileMenuOpen(false), []);

  return (
    <>
      <motion.header
        className="fixed top-0 left-0 right-0 z-50 animated-border-bottom"
        style={{
          backgroundColor: bgColor,
          backdropFilter: bgFilter,
          borderBottomWidth: "1px",
          borderBottomStyle: "solid",
          borderBottomColor: borderColor,
        }}
        role="banner"
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <motion.button
            onClick={handleLogoClick}
            className="flex items-center"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            aria-label="HookCut home"
          >
            <HookCutWordmark />
          </motion.button>

          {/* Desktop nav */}
          <nav className="hidden sm:flex items-center gap-1 relative" aria-label="Main navigation">
            {isAdmin && (
              <Link
                href="/dashboard"
                className={`relative px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  pathname === "/dashboard"
                    ? "text-white"
                    : "text-white/65 hover:text-white/90 hover:bg-white/[0.05]"
                }`}
              >
                Dashboard
                {pathname === "/dashboard" && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 rounded-full bg-[--color-primary]"
                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                  />
                )}
              </Link>
            )}
            {NAV_LINKS.map((link) => {
              const isActive = pathname.startsWith(`/${link.match}`);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "text-white"
                      : "text-white/65 hover:text-white/90 hover:bg-white/[0.05]"
                  }`}
                >
                  {link.label}
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 rounded-full bg-[--color-primary]"
                      transition={{ type: "spring", stiffness: 300, damping: 25 }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Right section */}
          <div className="flex items-center gap-3">
            {/* Credit balance (desktop) */}
            {balance !== null && (
              <Link
                href="/dashboard"
                className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-[--color-border-def] bg-[--color-surface-1] text-sm hover:bg-[--color-surface-2] transition-colors duration-200"
                aria-label={`${balance.toFixed(0)} minutes of credits remaining`}
              >
                <CreditCard className="w-3.5 h-3.5 text-[--color-muted]" aria-hidden="true" />
                <span className="font-semibold text-white/90 tabular-nums font-mono">
                  {balance.toFixed(0)}
                </span>
                <span className="text-white/35 text-xs">min</span>
              </Link>
            )}

            {/* Auth — desktop */}
            {status === "authenticated" && session?.user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    className="hidden sm:flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-white/[0.04] transition-colors duration-200 outline-none"
                    aria-label="User menu"
                  >
                    <Avatar className="h-7 w-7">
                      {session.user.image && (
                        <AvatarImage src={session.user.image} alt={session.user.name || "User"} />
                      )}
                      <AvatarFallback className="text-xs bg-[--color-surface-3]">
                        {userInitials}
                      </AvatarFallback>
                    </Avatar>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col gap-0.5">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-white/80 leading-none">
                          {session.user.name || "User"}
                        </p>
                        {isAdmin && (
                          <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-[--color-primary]/20 text-[--color-primary] border border-[--color-primary]/30">
                            Admin
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-white/35 leading-none mt-0.5">
                        {session.user.email}
                      </p>
                    </div>
                  </DropdownMenuLabel>

                  {balance !== null && (
                    <>
                      <DropdownMenuSeparator />
                      <div className="px-2 py-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-white/40 flex items-center gap-1.5">
                            <CreditCard className="w-3.5 h-3.5" aria-hidden="true" />
                            Credits
                          </span>
                          <span className="font-semibold text-white tabular-nums font-mono">
                            {balance.toFixed(0)}
                            <span className="text-white/35 font-normal ml-0.5 text-xs">min</span>
                          </span>
                        </div>
                      </div>
                    </>
                  )}

                  <DropdownMenuSeparator />

                  <DropdownMenuItem
                    onClick={() => router.push("/dashboard")}
                    className="cursor-pointer"
                  >
                    <LayoutDashboard className="w-4 h-4 mr-2 text-white/35" aria-hidden="true" />
                    Dashboard
                  </DropdownMenuItem>

                  <DropdownMenuItem
                    onClick={() => router.push("/settings")}
                    className="cursor-pointer"
                  >
                    <Settings className="w-4 h-4 mr-2 text-white/35" aria-hidden="true" />
                    Settings
                  </DropdownMenuItem>

                  <DropdownMenuSeparator />

                  <DropdownMenuItem
                    onClick={handleSignOut}
                    className="cursor-pointer text-red-400 focus:text-red-300"
                  >
                    <LogOut className="w-4 h-4 mr-2" aria-hidden="true" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : status === "unauthenticated" ? (
              <div className="hidden sm:flex items-center gap-1">
                <Link
                  href="/auth/login"
                  className="px-4 py-2 text-sm font-medium text-white/65 hover:text-white transition-colors rounded-lg hover:bg-white/[0.05]"
                >
                  Log In
                </Link>
                <Link
                  href="/auth/login"
                  className="btn-primary px-5 py-2 text-sm rounded-full font-semibold"
                >
                  Try for Free
                </Link>
              </div>
            ) : null}

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen((v) => !v)}
              className="sm:hidden flex items-center justify-center w-9 h-9 rounded-lg hover:bg-white/[0.05] transition-colors"
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? (
                <X className="w-5 h-5 text-white/60" aria-hidden="true" />
              ) : (
                <Menu className="w-5 h-5 text-white/60" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="fixed inset-0 z-40 sm:hidden"
          role="dialog"
          aria-label="Mobile navigation"
        >
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={closeMobileMenu}
            aria-hidden="true"
          />
          <div className="absolute right-0 top-16 bottom-0 w-72 glass-strong border-l border-[--color-border-def] p-6 overflow-y-auto">
            <nav className="flex flex-col gap-1 mb-6" aria-label="Mobile navigation">
              {isAdmin && (
                <Link
                  href="/dashboard"
                  onClick={closeMobileMenu}
                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    pathname === "/dashboard"
                      ? "text-white bg-[--color-primary]/10 border border-[--color-primary]/20"
                      : "text-white/50 hover:text-white hover:bg-white/[0.04]"
                  }`}
                >
                  Dashboard
                </Link>
              )}
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={closeMobileMenu}
                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    pathname.startsWith(`/${link.match}`)
                      ? "text-white bg-[--color-primary]/10 border border-[--color-primary]/20"
                      : "text-white/50 hover:text-white hover:bg-white/[0.04]"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </nav>

            {balance !== null && (
              <div className="glass rounded-xl p-4 mb-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-white/40 font-medium">Credits</span>
                  <span className="font-semibold text-white tabular-nums font-mono">
                    {balance.toFixed(0)}
                    <span className="text-white/35 font-normal ml-0.5 text-xs">min</span>
                  </span>
                </div>
              </div>
            )}

            {session?.user ? (
              <div className="border-t border-[--color-border-def] pt-4">
                <div className="flex items-center gap-3 mb-4 px-1">
                  <Avatar className="h-8 w-8">
                    {session.user.image && (
                      <AvatarImage src={session.user.image} alt="" aria-hidden="true" />
                    )}
                    <AvatarFallback className="text-xs bg-[--color-surface-3]">
                      {userInitials}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-white/80 truncate">
                        {session.user.name}
                      </p>
                      {isAdmin && (
                        <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-[--color-primary]/20 text-[--color-primary] border border-[--color-primary]/30 shrink-0">
                          Admin
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-white/30 truncate">{session.user.email}</p>
                  </div>
                </div>
                <button
                  onClick={handleSignOut}
                  className="w-full px-4 py-2.5 rounded-xl text-sm text-red-400 hover:bg-red-500/10 transition-colors text-left flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" aria-hidden="true" />
                  Sign Out
                </button>
              </div>
            ) : status === "unauthenticated" ? (
              <Link
                href="/auth/login"
                onClick={closeMobileMenu}
                className="btn-primary w-full text-center text-sm py-3 block rounded-xl"
              >
                Start Analyzing →
              </Link>
            ) : null}
          </div>
        </motion.div>
      )}
    </>
  );
}
