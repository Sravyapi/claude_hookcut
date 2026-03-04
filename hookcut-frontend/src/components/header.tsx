"use client";

import { useEffect, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { Settings, LogOut, LayoutDashboard, CreditCard, Menu, X } from "lucide-react";
import { api } from "@/lib/api";
import { useUser } from "@/components/providers";
import { Button } from "@/components/ui/button";
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
  { href: "/dashboard", label: "Dashboard" },
  { href: "/pricing", label: "Pricing" },
];

export default function Header({ onReset }: { onReset?: () => void }) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const { role } = useUser();
  const [balance, setBalance] = useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isAdmin = role === "admin";

  // Scroll-triggered header opacity
  const { scrollY } = useScroll();
  const headerBg = useTransform(scrollY, [0, 80], [0, 1]);
  const headerBorder = useTransform(scrollY, [0, 80], [0, 0.06]);
  const headerBgColor = useTransform(headerBg, (v) => `rgba(6, 6, 14, ${0.4 + v * 0.5})`);
  const headerBlur = useTransform(headerBg, (v) => `blur(${20 + v * 20}px) saturate(${1 + v * 0.4})`);
  const headerBorderColor = useTransform(headerBorder, (v) => `rgba(255, 255, 255, ${v})`);

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

  const handleLogoClick = () => {
    if (onReset) {
      onReset();
    } else {
      router.push("/");
    }
  };

  return (
    <>
      <motion.header
        className="fixed top-0 left-0 right-0 z-50 animated-border-bottom"
        style={{
          backgroundColor: headerBgColor,
          backdropFilter: headerBlur,
          borderBottomColor: headerBorderColor,
        }}
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Left: Logo */}
          <motion.button
            onClick={handleLogoClick}
            className="flex items-center gap-3 group"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            aria-label="HookCut home"
          >
            <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-violet-500/20 group-hover:shadow-violet-500/40 transition-shadow duration-300 overflow-hidden">
              <span className="relative z-10">H</span>
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-violet-400 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              <span className="gradient-text">Hook</span>
              <span className="text-white/80">Cut</span>
            </span>
          </motion.button>

          {/* Center: Navigation Links (desktop) */}
          <nav className="hidden sm:flex items-center gap-1 relative">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "text-white"
                      : "text-white/50 hover:text-white hover:bg-white/[0.05]"
                  }`}
                >
                  {link.label}
                  {isActive && (
                    <motion.div
                      layoutId="nav-indicator"
                      className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 rounded-full bg-violet-500"
                      transition={{ type: "spring", stiffness: 300, damping: 25 }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Right: Balance + User */}
          <div className="flex items-center gap-3">
            {/* Credit Balance (desktop) */}
            {balance !== null && (
              <Link
                href="/dashboard"
                className="hidden sm:flex items-center gap-2.5 px-4 py-2 rounded-xl glass text-sm hover:bg-white/[0.06] transition-colors duration-200"
              >
                <svg
                  className="w-4 h-4 text-violet-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span className="text-white/40 text-xs font-medium">Credits</span>
                <span className="font-semibold text-white tabular-nums">
                  {balance.toFixed(0)}
                  <span className="text-white/40 font-normal ml-0.5">min</span>
                </span>
              </Link>
            )}

            {/* Auth Section (desktop) */}
            {status === "authenticated" && session?.user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="hidden sm:flex items-center gap-2 rounded-xl px-2 py-1.5 hover:bg-white/[0.05] transition-colors duration-200 outline-none" aria-label="User menu">
                    <Avatar className="h-8 w-8">
                      {session.user.image && (
                        <AvatarImage
                          src={session.user.image}
                          alt={session.user.name || "User"}
                        />
                      )}
                      <AvatarFallback className="text-xs">
                        {userInitials}
                      </AvatarFallback>
                    </Avatar>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-white/80 leading-none">
                          {session.user.name || "User"}
                        </p>
                        {isAdmin && (
                          <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-violet-500/20 text-violet-300 border border-violet-500/30">
                            Admin
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-white/40 leading-none">
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
                            <CreditCard className="w-3.5 h-3.5" />
                            Credits
                          </span>
                          <span className="font-semibold text-white tabular-nums">
                            {balance.toFixed(0)}
                            <span className="text-white/40 font-normal ml-0.5 text-xs">min</span>
                          </span>
                        </div>
                      </div>
                    </>
                  )}

                  <DropdownMenuSeparator />

                  <DropdownMenuItem onClick={() => router.push("/dashboard")} className="cursor-pointer">
                    <LayoutDashboard className="w-4 h-4 mr-2 text-white/40" />
                    Dashboard
                  </DropdownMenuItem>

                  <DropdownMenuItem onClick={() => router.push("/settings")} className="cursor-pointer">
                    <Settings className="w-4 h-4 mr-2 text-white/40" />
                    Settings
                  </DropdownMenuItem>

                  <DropdownMenuSeparator />

                  <DropdownMenuItem
                    onClick={() => signOut({ callbackUrl: "/" })}
                    className="cursor-pointer text-red-400 focus:text-red-300"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : status === "unauthenticated" ? (
              <Button variant="secondary" size="sm" asChild className="hidden sm:flex">
                <Link href="/auth/login">Sign In</Link>
              </Button>
            ) : null}

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="sm:hidden flex items-center justify-center w-9 h-9 rounded-lg hover:bg-white/[0.05] transition-colors"
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            >
              {mobileMenuOpen ? (
                <X className="w-5 h-5 text-white/60" />
              ) : (
                <Menu className="w-5 h-5 text-white/60" />
              )}
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile slide-out nav */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="fixed inset-0 z-40 sm:hidden"
        >
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="absolute right-0 top-16 bottom-0 w-72 glass-strong border-l border-white/[0.06] p-6">
            <nav className="flex flex-col gap-2 mb-6">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    pathname === link.href
                      ? "text-white bg-violet-500/10 border border-violet-500/20"
                      : "text-white/50 hover:text-white hover:bg-white/[0.05]"
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
                  <span className="font-semibold text-white tabular-nums">
                    {balance.toFixed(0)}
                    <span className="text-white/40 font-normal ml-0.5 text-xs">min</span>
                  </span>
                </div>
              </div>
            )}

            {session?.user && (
              <div className="border-t border-white/[0.06] pt-4">
                <div className="flex items-center gap-3 mb-4 px-1">
                  <Avatar className="h-8 w-8">
                    {session.user.image && <AvatarImage src={session.user.image} alt={session?.user?.name || "User avatar"} />}
                    <AvatarFallback className="text-xs">{userInitials}</AvatarFallback>
                  </Avatar>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-white/80 truncate">{session.user.name}</p>
                      {isAdmin && (
                        <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-violet-500/20 text-violet-300 border border-violet-500/30 shrink-0">
                          Admin
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-white/30 truncate">{session.user.email}</p>
                  </div>
                </div>
                <button
                  onClick={() => signOut({ callbackUrl: "/" })}
                  className="w-full px-4 py-2.5 rounded-xl text-sm text-red-400 hover:bg-red-500/10 transition-colors text-left flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            )}

            {status === "unauthenticated" && (
              <Link
                href="/auth/login"
                onClick={() => setMobileMenuOpen(false)}
                className="btn-primary w-full text-center text-sm py-3 block"
              >
                Sign In
              </Link>
            )}
          </div>
        </motion.div>
      )}
    </>
  );
}
