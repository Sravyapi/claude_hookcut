"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import type { AdminUser, AdminUserList } from "@/lib/types";
import { Skeleton } from "@/components/ui/skeleton";
import { staggerContainer, fadeUpItem } from "@/lib/motion";

/* ─── Role config ─── */
const ROLE_OPTIONS = ["user", "admin"];

function roleBadge(role: string) {
  if (role === "admin")
    return "bg-violet-500/15 text-violet-300 border-violet-500/25";
  return "bg-white/5 text-white/50 border-white/10";
}

function tierBadge(tier: string) {
  if (tier === "pro")
    return "bg-emerald-500/15 text-emerald-300 border-emerald-500/25";
  if (tier === "business")
    return "bg-blue-500/15 text-blue-300 border-blue-500/25";
  return "bg-white/5 text-white/50 border-white/10";
}

/* ─── Confirmation Dialog ─── */
function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-[#0a0a14] border border-white/10 rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl"
      >
        <h3 className="text-base font-semibold text-white mb-2">{title}</h3>
        <p className="text-sm text-white/50 mb-6">{message}</p>
        <div className="flex items-center gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-xl text-sm text-white/50 hover:text-white/70 hover:bg-white/[0.04] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded-xl text-sm font-medium bg-violet-500/20 text-violet-300 border border-violet-500/30 hover:bg-violet-500/30 transition-colors"
          >
            {confirmLabel}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

/* ─── Main ─── */
export default function AdminUsersPage() {
  const { toast } = useToast();
  const [data, setData] = useState<AdminUserList | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  /* Role change confirmation state */
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingRoleChange, setPendingRoleChange] = useState<{
    userId: string;
    email: string;
    newRole: string;
  } | null>(null);
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);

  const fetchUsers = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const result = await api.adminUsers(p);
      setData(result);
    } catch (err) {
      console.warn("Failed to load users:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchUsers(page);
  }, [page, fetchUsers]);

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 1;

  /* ─── Role change handlers ─── */
  const handleRoleSelect = (user: AdminUser, newRole: string) => {
    if (newRole === user.role) return;
    setPendingRoleChange({ userId: user.id, email: user.email, newRole });
    setConfirmOpen(true);
  };

  const handleRoleConfirm = async () => {
    if (!pendingRoleChange) return;
    setConfirmOpen(false);
    setUpdatingUserId(pendingRoleChange.userId);

    try {
      await api.adminUpdateRole(pendingRoleChange.userId, pendingRoleChange.newRole);
      await fetchUsers(page);
    } catch (err) {
      console.warn("Failed to update role:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setUpdatingUserId(null);
      setPendingRoleChange(null);
    }
  };

  const handleRoleCancel = () => {
    setConfirmOpen(false);
    setPendingRoleChange(null);
  };

  return (
    <div className="space-y-6">
      {/* ─── Page header ─── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-2xl font-bold text-white">User Management</h1>
        <p className="text-white/40 text-sm mt-0.5">
          View and manage platform users
          {data && (
            <span className="text-white/25 ml-2">
              ({data.total} total)
            </span>
          )}
        </p>
      </motion.div>

      {/* ─── Users table ─── */}
      <motion.div
        className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
      >
        {loading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : data && data.users.length > 0 ? (
          <>
            {/* Table header */}
            <div className="grid grid-cols-[2fr_1fr_1fr_0.8fr_0.8fr_1.2fr] gap-4 px-6 py-3 text-[10px] font-medium text-white/25 uppercase tracking-wider border-b border-white/[0.06]">
              <span>Email</span>
              <span>Role</span>
              <span>Plan Tier</span>
              <span>Currency</span>
              <span className="text-right">Sessions</span>
              <span className="text-right">Joined</span>
            </div>

            {/* Table rows */}
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="show"
            >
              {data.users.map((user) => {
                const dateStr = new Date(user.created_at).toLocaleDateString(
                  undefined,
                  { month: "short", day: "numeric", year: "numeric" }
                );

                return (
                  <motion.div
                    key={user.id}
                    variants={fadeUpItem}
                    className="grid grid-cols-[2fr_1fr_1fr_0.8fr_0.8fr_1.2fr] gap-4 px-6 py-3.5 hover:bg-white/[0.02] transition-colors border-b border-white/[0.03] last:border-0 items-center"
                  >
                    {/* Email */}
                    <span className="text-sm text-white/70 truncate">
                      {user.email}
                    </span>

                    {/* Role selector */}
                    <div className="relative">
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleSelect(user, e.target.value)}
                        disabled={updatingUserId === user.id}
                        className={`appearance-none text-[11px] px-2.5 py-1 rounded-full border font-medium cursor-pointer bg-transparent outline-none transition-colors ${roleBadge(user.role)} ${
                          updatingUserId === user.id ? "opacity-50" : ""
                        }`}
                      >
                        {ROLE_OPTIONS.map((r) => (
                          <option
                            key={r}
                            value={r}
                            className="bg-[#0a0a14] text-white"
                          >
                            {r}
                          </option>
                        ))}
                      </select>
                      {updatingUserId === user.id && (
                        <span className="absolute right-0 top-1/2 -translate-y-1/2 text-[10px] text-white/30">
                          ...
                        </span>
                      )}
                    </div>

                    {/* Plan tier */}
                    <span>
                      <span
                        className={`text-[11px] px-2.5 py-0.5 rounded-full border font-medium ${tierBadge(user.plan_tier)}`}
                      >
                        {user.plan_tier}
                      </span>
                    </span>

                    {/* Currency */}
                    <span className="text-xs text-white/40">
                      {user.currency}
                    </span>

                    {/* Session count */}
                    <span className="text-xs text-white/40 tabular-nums text-right">
                      {user.session_count}
                    </span>

                    {/* Joined date */}
                    <span className="text-xs text-white/30 tabular-nums text-right">
                      {dateStr}
                    </span>
                  </motion.div>
                );
              })}
            </motion.div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-white/[0.06]">
                <p className="text-xs text-white/30">
                  Page {page} of {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-white/50 hover:text-white/70 bg-white/[0.04] border border-white/[0.06] hover:bg-white/[0.06] transition-colors disabled:opacity-30 disabled:pointer-events-none"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                    Previous
                  </button>
                  <button
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-white/50 hover:text-white/70 bg-white/[0.04] border border-white/[0.06] hover:bg-white/[0.06] transition-colors disabled:opacity-30 disabled:pointer-events-none"
                  >
                    Next
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="py-16 text-center">
            <p className="text-sm text-white/30">No users found.</p>
          </div>
        )}
      </motion.div>

      {/* ─── Role change confirmation dialog ─── */}
      <ConfirmDialog
        open={confirmOpen}
        title="Change User Role"
        message={
          pendingRoleChange
            ? `Are you sure you want to change ${pendingRoleChange.email}'s role to "${pendingRoleChange.newRole}"?`
            : ""
        }
        confirmLabel="Change Role"
        onConfirm={handleRoleConfirm}
        onCancel={handleRoleCancel}
      />
    </div>
  );
}
