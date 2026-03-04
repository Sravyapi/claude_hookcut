"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  History,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { PromptRuleHistory } from "@/lib/types";

interface RuleHistoryProps {
  showHistory: boolean;
  loadingHistory: boolean;
  history: PromptRuleHistory | null;
  reverting: string | null;
  onToggleHistory: () => void;
  onRevert: (versionId: string) => void;
}

export default function RuleHistoryPanel({
  showHistory,
  loadingHistory,
  history,
  reverting,
  onToggleHistory,
  onRevert,
}: RuleHistoryProps) {
  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
      <button
        onClick={onToggleHistory}
        aria-expanded={showHistory}
        aria-label="Toggle version history"
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2 text-sm font-semibold text-white/70">
          <History className="w-4 h-4 text-violet-400" />
          Version History
        </div>
        {showHistory ? (
          <ChevronUp className="w-4 h-4 text-white/30" />
        ) : (
          <ChevronDown className="w-4 h-4 text-white/30" />
        )}
      </button>

      <AnimatePresence>
        {showHistory && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-4 border-t border-white/[0.05]">
              {loadingHistory ? (
                <div className="space-y-3 pt-4">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div
                      key={i}
                      className="h-16 bg-white/[0.03] rounded-xl animate-pulse"
                    />
                  ))}
                </div>
              ) : history &&
                history.versions.length > 0 ? (
                <div className="space-y-2 pt-4 max-h-[300px] overflow-y-auto">
                  {history.versions.map((version, idx) => (
                    <div
                      key={version.id}
                      className="flex items-start justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04] transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium text-white/60">
                            Version {version.version}
                          </span>
                          {idx === 0 && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300">
                              Current
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-white/30 mb-1">
                          {new Date(
                            version.created_at
                          ).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </p>
                        <p className="text-xs text-white/40 line-clamp-2">
                          {version.content.slice(0, 120)}
                          {version.content.length > 120
                            ? "..."
                            : ""}
                        </p>
                      </div>
                      {idx !== 0 && (
                        <button
                          onClick={() =>
                            onRevert(version.id)
                          }
                          disabled={reverting === version.id}
                          aria-label={`Revert to version ${version.version}`}
                          className="shrink-0 ml-3 px-3 py-1.5 rounded-lg text-[11px] text-violet-300 border border-violet-500/20 hover:bg-violet-500/10 transition-all duration-200 disabled:opacity-50"
                        >
                          {reverting === version.id
                            ? "Reverting..."
                            : "Revert"}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-white/30 text-center py-6">
                  No version history available
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
