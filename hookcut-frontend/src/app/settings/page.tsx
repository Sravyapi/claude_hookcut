"use client";

import { useEffect, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { User, Mail, DollarSign, CreditCard, Clock, Zap, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import type { CreditBalance, UserProfile } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";

type Tab = "account" | "billing";

const TAB_ITEMS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "account", label: "Account", icon: <User className="w-3.5 h-3.5" /> },
  { id: "billing", label: "Billing", icon: <CreditCard className="w-3.5 h-3.5" /> },
];

function BalanceRow({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/[0.04] last:border-0">
      <div className="flex items-center gap-3 text-white/50">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className="text-right">
        <span className="text-sm font-semibold text-white/80 tabular-nums">{value}</span>
        {sub && (
          <span className="text-xs text-white/30 ml-1">{sub}</span>
        )}
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { data: session, status: authStatus } = useSession();
  const router = useRouter();

  const [activeTab, setActiveTab] = useState<Tab>("account");
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingBalance, setLoadingBalance] = useState(true);
  const [currency, setCurrency] = useState<"USD" | "INR">("USD");
  const [savingCurrency, setSavingCurrency] = useState(false);

  useEffect(() => {
    if (authStatus === "unauthenticated") router.push("/auth/login");
  }, [authStatus, router]);

  useEffect(() => {
    if (authStatus !== "authenticated") return;

    setLoadingProfile(true);
    api
      .getProfile()
      .then((data) => {
        setProfile(data);
        if (data.currency === "USD" || data.currency === "INR") setCurrency(data.currency);
      })
      .catch((err) => {
        console.error("Failed to load profile:", err);
        if (session?.user) {
          setProfile({ id: "", email: session.user.email || "", plan_tier: "free", currency: "USD", role: "user", created_at: "" });
        }
      })
      .finally(() => setLoadingProfile(false));

    setLoadingBalance(true);
    api
      .getBalance()
      .then(setBalance)
      .catch((err) => console.warn("Failed to load balance:", err))
      .finally(() => setLoadingBalance(false));
  }, [authStatus, session]);

  const handleCurrencyChange = async (c: "USD" | "INR") => {
    if (c === currency) return;
    setSavingCurrency(true);
    try {
      await api.updateCurrency(c);
      setCurrency(c);
      if (profile) setProfile({ ...profile, currency: c });
    } catch (err) {
      console.warn("Failed to update currency:", err);
    } finally {
      setSavingCurrency(false);
    }
  };

  if (authStatus === "loading") {
    return (
      <main className="pt-24 pb-12">
        <div className="max-w-2xl mx-auto px-6 space-y-4">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-96 w-full" />
        </div>
      </main>
    );
  }

  if (authStatus === "unauthenticated") return null;

  const tierLabel =
    (profile?.plan_tier || "free").charAt(0).toUpperCase() +
    (profile?.plan_tier || "free").slice(1);

  const userInitials = session?.user?.name
    ? session.user.name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)
    : session?.user?.email?.[0]?.toUpperCase() ?? "U";

  return (
    <main className="pt-24 pb-12">
      <div className="max-w-2xl mx-auto px-6">
        {/* Header */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-white/40 text-sm mt-0.5">
            Manage your account and billing preferences
          </p>
        </motion.div>

        {/* Custom tabs */}
        <motion.div
          className="mb-6"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
        >
          <div className="flex gap-1 p-1 glass rounded-xl w-fit">
            {TAB_ITEMS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                  activeTab === tab.id
                    ? "text-white"
                    : "text-white/40 hover:text-white/60"
                }`}
              >
                {activeTab === tab.id && (
                  <motion.div
                    layoutId="tab-bg"
                    className="absolute inset-0 bg-white/[0.07] rounded-lg"
                    transition={{ type: "spring", stiffness: 300, damping: 28 }}
                  />
                )}
                <span className="relative z-10 flex items-center gap-1.5">
                  {tab.icon}
                  {tab.label}
                </span>
              </button>
            ))}
          </div>
        </motion.div>

        {/* Tab content with AnimatePresence */}
        <AnimatePresence mode="wait">
          {activeTab === "account" && (
            <motion.div
              key="account"
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }}
              transition={{ duration: 0.2 }}
              className="space-y-4"
            >
              {/* Account card */}
              <div className="glass-card rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-white/70 mb-5">
                  Account Information
                </h2>

                {loadingProfile ? (
                  <div className="space-y-4">
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                  </div>
                ) : (
                  <>
                    {/* Avatar + name */}
                    {session?.user && (
                      <div className="flex items-center gap-4 mb-6 p-4 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                        <Avatar className="h-12 w-12">
                          {session.user.image && (
                            <AvatarImage src={session.user.image} alt="User avatar" />
                          )}
                          <AvatarFallback className="text-sm font-semibold">
                            {userInitials}
                          </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0">
                          <p className="font-semibold text-white/90 truncate">
                            {session.user.name || "User"}
                          </p>
                          <p className="text-xs text-white/40 truncate">
                            {session.user.email}
                          </p>
                        </div>
                        <span className="ml-auto text-[10px] px-2.5 py-1 rounded-full bg-violet-500/10 text-violet-300 border border-violet-500/20 shrink-0">
                          {tierLabel}
                        </span>
                      </div>
                    )}

                    {/* Email field */}
                    <div className="mb-5">
                      <label className="flex items-center gap-2 text-xs font-medium text-white/40 mb-2">
                        <Mail className="w-3.5 h-3.5" />
                        Email Address
                      </label>
                      <div className="px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.06] text-sm text-white/60">
                        {profile?.email || session?.user?.email || "Not available"}
                      </div>
                      <p className="text-[11px] text-white/25 mt-1.5">
                        Managed by your authentication provider
                      </p>
                    </div>

                    {/* Currency preference */}
                    <div>
                      <label className="flex items-center gap-2 text-xs font-medium text-white/40 mb-2">
                        <DollarSign className="w-3.5 h-3.5" />
                        Currency Preference
                      </label>
                      <div className="flex items-center gap-2">
                        {(["USD", "INR"] as const).map((c) => (
                          <button
                            key={c}
                            onClick={() => handleCurrencyChange(c)}
                            disabled={savingCurrency}
                            className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                              currency === c
                                ? "bg-violet-500/15 text-violet-300 border border-violet-500/35"
                                : "bg-white/[0.03] text-white/45 border border-white/[0.06] hover:bg-white/[0.06] hover:text-white/60"
                            }`}
                          >
                            {c === "USD" ? "$ USD" : "₹ INR"}
                          </button>
                        ))}
                        {savingCurrency && (
                          <span className="text-xs text-white/30">Saving...</span>
                        )}
                      </div>
                      <p className="text-[11px] text-white/25 mt-1.5">
                        Prices on the billing page will use this currency
                      </p>
                    </div>
                  </>
                )}
              </div>

              {/* Danger zone */}
              <div className="glass-card rounded-2xl p-6 border border-red-500/10">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-4 h-4 text-red-400/70" />
                  <h2 className="text-sm font-semibold text-red-400/70">Danger Zone</h2>
                </div>
                <p className="text-xs text-white/35 mb-4 leading-relaxed">
                  Signing out will end your current session. To delete your account,
                  please contact support.
                </p>
                <button
                  onClick={() => signOut({ callbackUrl: "/" })}
                  className="text-sm px-4 py-2 rounded-xl border border-red-500/20 text-red-400/80 hover:bg-red-500/10 transition-colors duration-200"
                >
                  Sign Out
                </button>
              </div>
            </motion.div>
          )}

          {activeTab === "billing" && (
            <motion.div
              key="billing"
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }}
              transition={{ duration: 0.2 }}
              className="space-y-4"
            >
              {/* Current plan */}
              <div className="glass-card rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-white/70 mb-4">
                  Current Plan
                </h2>
                {loadingProfile ? (
                  <Skeleton className="h-16 w-full" />
                ) : (
                  <div className="flex items-center justify-between p-4 rounded-xl bg-violet-500/8 border border-violet-500/15">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-violet-500/15 flex items-center justify-center">
                        <CreditCard className="w-4.5 h-4.5 text-violet-400" />
                      </div>
                      <div>
                        <p className="font-semibold text-white text-sm">{tierLabel}</p>
                        <p className="text-xs text-white/35 mt-0.5">
                          {profile?.plan_tier === "free"
                            ? "Free tier with limited features"
                            : `Active ${tierLabel} subscription`}
                        </p>
                      </div>
                    </div>
                    <Button variant="secondary" size="sm" asChild>
                      <Link href="/pricing">Change Plan</Link>
                    </Button>
                  </div>
                )}
              </div>

              {/* Credit balance */}
              <div className="glass-card rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-semibold text-white/70">Credit Balance</h2>
                  <Button variant="secondary" size="sm" asChild>
                    <Link href="/pricing">Top Up</Link>
                  </Button>
                </div>

                {loadingBalance ? (
                  <div className="space-y-2">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : balance ? (
                  <div>
                    {/* Total highlight */}
                    <div className="flex items-center justify-between p-4 rounded-xl bg-violet-500/8 border border-violet-500/15 mb-4">
                      <div className="flex items-center gap-2 text-violet-300">
                        <Clock className="w-4 h-4" />
                        <span className="text-sm font-medium">Total Available</span>
                      </div>
                      <span className="text-xl font-bold text-white tabular-nums">
                        {balance.total_available.toFixed(1)}
                        <span className="text-sm text-white/35 font-normal ml-1">min</span>
                      </span>
                    </div>

                    {/* Breakdown */}
                    <div className="px-1">
                      <BalanceRow
                        icon={<CreditCard className="w-4 h-4" />}
                        label="Paid Minutes"
                        value={balance.paid_minutes_remaining.toFixed(1)}
                        sub={`/ ${balance.paid_minutes_total.toFixed(0)} min`}
                      />
                      <BalanceRow
                        icon={<Zap className="w-4 h-4" />}
                        label="Pay-As-You-Go"
                        value={balance.payg_minutes_remaining.toFixed(1)}
                        sub="min"
                      />
                      <BalanceRow
                        icon={<Clock className="w-4 h-4" />}
                        label="Free Minutes"
                        value={balance.free_minutes_remaining.toFixed(1)}
                        sub={`/ ${balance.free_minutes_total.toFixed(0)} min`}
                      />
                    </div>
                  </div>
                ) : (
                  <p className="text-white/35 text-sm">Unable to load balance.</p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
