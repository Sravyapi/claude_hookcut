"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  Plus,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  PromptRule,
  PromptRuleHistory,
  PromptPreview,
} from "@/lib/types";
import { useToast } from "@/components/ui/use-toast";
import { staggerContainer, fadeUpItem } from "@/lib/motion";
import RuleEditor from "./rule-editor";
import RuleHistoryPanel from "./rule-history";
import PromptPreviewPanel from "./prompt-preview";

/* ─── Main Page ─── */

export default function PromptRuleEnginePage() {
  const { toast } = useToast();
  const [rules, setRules] = useState<PromptRule[]>([]);
  const [selectedRule, setSelectedRule] = useState<PromptRule | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [seeding, setSeeding] = useState(false);

  // Editor state
  const [editTitle, setEditTitle] = useState("");
  const [editContent, setEditContent] = useState("");
  const [editActive, setEditActive] = useState(true);

  // Version history
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<PromptRuleHistory | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [reverting, setReverting] = useState<string | null>(null);

  // Prompt preview
  const [previewNiche, setPreviewNiche] = useState("Generic");
  const [previewLanguage, setPreviewLanguage] = useState("English");
  const [preview, setPreview] = useState<PromptPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  // New custom rule
  const [showNewRule, setShowNewRule] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [creatingRule, setCreatingRule] = useState(false);

  const fetchRules = useCallback(async () => {
    try {
      const data = await api.adminRules();
      setRules(data.rules);
    } catch (err) {
      console.warn("Failed to load rules:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  // Sync editor when a rule is selected
  useEffect(() => {
    if (selectedRule) {
      setEditTitle(selectedRule.title);
      setEditContent(selectedRule.content);
      setEditActive(selectedRule.is_active);
      setShowHistory(false);
      setHistory(null);
    }
  }, [selectedRule]);

  const baseRules = rules.filter((r) => r.is_base_rule);
  const customRules = rules.filter((r) => !r.is_base_rule);

  /* ─── Handlers ─── */

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const data = await api.adminSeedRules();
      setRules(data.rules);
    } catch (err) {
      console.warn("Failed to seed rules:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setSeeding(false);
    }
  };

  const handleSave = async () => {
    if (!selectedRule) return;
    setSaving(true);
    try {
      const updated = await api.adminUpdateRule(selectedRule.id, {
        title: editTitle,
        content: editContent,
        is_active: editActive,
      });
      setSelectedRule(updated);
      setRules((prev) =>
        prev.map((r) => (r.id === updated.id ? updated : r))
      );
    } catch (err) {
      console.warn("Failed to save rule:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedRule || selectedRule.is_base_rule) return;
    setDeleting(true);
    try {
      await api.adminDeleteRule(selectedRule.id);
      setRules((prev) => prev.filter((r) => r.id !== selectedRule.id));
      setSelectedRule(null);
    } catch (err) {
      console.warn("Failed to delete rule:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setDeleting(false);
    }
  };

  const handleToggleHistory = async () => {
    if (!selectedRule) return;
    if (showHistory) {
      setShowHistory(false);
      return;
    }
    setShowHistory(true);
    setLoadingHistory(true);
    try {
      const data = await api.adminRuleHistory(selectedRule.rule_key);
      setHistory(data);
    } catch (err) {
      console.warn("Failed to load history:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleRevert = async (versionId: string) => {
    if (!selectedRule) return;
    setReverting(versionId);
    try {
      const reverted = await api.adminRevertRule(selectedRule.id, versionId);
      setSelectedRule(reverted);
      setRules((prev) =>
        prev.map((r) => (r.id === reverted.id ? reverted : r))
      );
      setShowHistory(false);
    } catch (err) {
      console.warn("Failed to revert rule:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setReverting(null);
    }
  };

  const handlePreview = async () => {
    setLoadingPreview(true);
    try {
      const data = await api.adminPreviewPrompt(previewNiche, previewLanguage);
      setPreview(data);
    } catch (err) {
      console.warn("Failed to preview prompt:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleCreateRule = async () => {
    if (!newTitle.trim() || !newContent.trim()) return;
    setCreatingRule(true);
    try {
      const created = await api.adminCreateRule({
        title: newTitle,
        content: newContent,
      });
      setRules((prev) => [...prev, created]);
      setNewTitle("");
      setNewContent("");
      setShowNewRule(false);
      setSelectedRule(created);
    } catch (err) {
      console.warn("Failed to create rule:", err);
      toast({ title: "Error", description: "Failed to load data. Please try again.", variant: "destructive" });
    } finally {
      setCreatingRule(false);
    }
  };

  /* ─── Render ─── */

  return (
    <div className="space-y-6">
        {/* Header */}
        <motion.div
          className="flex items-center justify-between mb-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <BookOpen className="w-6 h-6 text-violet-400" />
              Prompt Rule Engine
            </h1>
            <p className="text-white/40 text-sm mt-0.5">
              Manage base and custom prompt rules for hook extraction
            </p>
          </div>
          {rules.length === 0 && !loading && (
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-500/15 text-violet-300 border border-violet-500/30 hover:bg-violet-500/25 transition-all duration-200 text-sm font-medium disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              {seeding ? "Seeding..." : "Seed Base Rules"}
            </button>
          )}
        </motion.div>

        {/* Main two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left panel: Rules list (40%) */}
          <motion.div
            className="lg:col-span-2 space-y-4"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
          >
            {/* Base Rules */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/[0.05]">
                <h2 className="text-sm font-semibold text-white/70">
                  Base Rules (A-Q)
                </h2>
                <p className="text-[11px] text-white/30 mt-0.5">
                  {baseRules.length} rules
                </p>
              </div>
              {loading ? (
                <div className="p-4 space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div
                      key={i}
                      className="h-16 bg-white/[0.03] rounded-xl animate-pulse"
                    />
                  ))}
                </div>
              ) : (
                <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="show"
                  className="p-2 max-h-[400px] overflow-y-auto"
                >
                  {baseRules.map((rule) => (
                    <motion.button
                      key={rule.id}
                      variants={fadeUpItem}
                      onClick={() => setSelectedRule(rule)}
                      className={`w-full text-left p-3 rounded-xl transition-all duration-200 mb-1 ${
                        selectedRule?.id === rule.id
                          ? "bg-violet-500/10 border border-violet-500/25"
                          : "hover:bg-white/[0.03] border border-transparent"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-300 border border-violet-500/20 font-mono font-medium">
                          {rule.rule_key}
                        </span>
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                            rule.is_active
                              ? "bg-emerald-500/15 text-emerald-300"
                              : "bg-red-500/15 text-red-300"
                          }`}
                        >
                          {rule.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>
                      <p className="text-sm text-white/80 font-medium truncate">
                        {rule.title}
                      </p>
                      <p className="text-xs text-white/30 mt-0.5 line-clamp-1">
                        {rule.content.slice(0, 80)}
                        {rule.content.length > 80 ? "..." : ""}
                      </p>
                    </motion.button>
                  ))}
                </motion.div>
              )}
            </div>

            {/* Custom Rules */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-white/[0.05]">
                <h2 className="text-sm font-semibold text-white/70">
                  Custom Rules
                </h2>
                <p className="text-[11px] text-white/30 mt-0.5">
                  {customRules.length} rules
                </p>
              </div>
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="show"
                className="p-2 max-h-[300px] overflow-y-auto"
              >
                {customRules.length === 0 && !loading && (
                  <p className="text-xs text-white/25 text-center py-6">
                    No custom rules yet
                  </p>
                )}
                {customRules.map((rule) => (
                  <motion.button
                    key={rule.id}
                    variants={fadeUpItem}
                    onClick={() => setSelectedRule(rule)}
                    className={`w-full text-left p-3 rounded-xl transition-all duration-200 mb-1 ${
                      selectedRule?.id === rule.id
                        ? "bg-violet-500/10 border border-violet-500/25"
                        : "hover:bg-white/[0.03] border border-transparent"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/20 font-mono font-medium">
                        {rule.rule_key}
                      </span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                          rule.is_active
                            ? "bg-emerald-500/15 text-emerald-300"
                            : "bg-red-500/15 text-red-300"
                        }`}
                      >
                        {rule.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <p className="text-sm text-white/80 font-medium truncate">
                      {rule.title}
                    </p>
                    <p className="text-xs text-white/30 mt-0.5 line-clamp-1">
                      {rule.content.slice(0, 80)}
                      {rule.content.length > 80 ? "..." : ""}
                    </p>
                  </motion.button>
                ))}
              </motion.div>
              {/* Add Custom Rule button */}
              <div className="p-3 border-t border-white/[0.05]">
                <button
                  onClick={() => {
                    setShowNewRule(true);
                    setSelectedRule(null);
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-dashed border-white/10 text-white/40 hover:text-white/60 hover:border-white/20 hover:bg-white/[0.02] transition-all duration-200 text-sm"
                >
                  <Plus className="w-4 h-4" />
                  Add Custom Rule
                </button>
              </div>
            </div>
          </motion.div>

          {/* Right panel: Editor (60%) */}
          <motion.div
            className="lg:col-span-3 space-y-4"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <AnimatePresence mode="wait">
              {/* New rule form */}
              {showNewRule && !selectedRule && (
                <motion.div
                  key="new-rule"
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.2 }}
                  className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
                >
                  <h2 className="text-sm font-semibold text-white/70 mb-5 flex items-center gap-2">
                    <Plus className="w-4 h-4 text-violet-400" />
                    New Custom Rule
                  </h2>

                  <div className="space-y-4">
                    <div>
                      <label className="text-xs font-medium text-white/40 mb-2 block">
                        Title
                      </label>
                      <input
                        type="text"
                        value={newTitle}
                        onChange={(e) => setNewTitle(e.target.value)}
                        placeholder="Rule title..."
                        className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm text-white/80 placeholder-white/20 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-white/40 mb-2 block">
                        Content
                      </label>
                      <textarea
                        value={newContent}
                        onChange={(e) => setNewContent(e.target.value)}
                        placeholder="Rule content..."
                        rows={8}
                        className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm text-white/80 placeholder-white/20 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all font-mono min-h-[200px] resize-y"
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={handleCreateRule}
                        disabled={
                          creatingRule ||
                          !newTitle.trim() ||
                          !newContent.trim()
                        }
                        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-500/15 text-violet-300 border border-violet-500/30 hover:bg-violet-500/25 transition-all duration-200 text-sm font-medium disabled:opacity-50"
                      >
                        <Plus className="w-4 h-4" />
                        {creatingRule ? "Creating..." : "Create Rule"}
                      </button>
                      <button
                        onClick={() => {
                          setShowNewRule(false);
                          setNewTitle("");
                          setNewContent("");
                        }}
                        className="px-4 py-2.5 rounded-xl text-sm text-white/40 hover:text-white/60 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Rule editor */}
              {selectedRule && (
                <motion.div
                  key={`editor-${selectedRule.id}`}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-4"
                >
                  <RuleEditor
                    selectedRule={selectedRule}
                    editTitle={editTitle}
                    editContent={editContent}
                    editActive={editActive}
                    saving={saving}
                    deleting={deleting}
                    onEditTitle={setEditTitle}
                    onEditContent={setEditContent}
                    onEditActive={setEditActive}
                    onSave={handleSave}
                    onDelete={handleDelete}
                  />

                  <RuleHistoryPanel
                    showHistory={showHistory}
                    loadingHistory={loadingHistory}
                    history={history}
                    reverting={reverting}
                    onToggleHistory={handleToggleHistory}
                    onRevert={handleRevert}
                  />
                </motion.div>
              )}

              {/* Empty state */}
              {!selectedRule && !showNewRule && (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-12 flex flex-col items-center justify-center text-center"
                >
                  <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center mb-4">
                    <BookOpen className="w-7 h-7 text-white/15" />
                  </div>
                  <p className="text-white/40 text-sm mb-1">
                    Select a rule to edit
                  </p>
                  <p className="text-white/25 text-xs">
                    Click any rule from the list to view and modify it
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        {/* Prompt Preview Panel (bottom) */}
        <PromptPreviewPanel
          previewNiche={previewNiche}
          previewLanguage={previewLanguage}
          preview={preview}
          loadingPreview={loadingPreview}
          onNicheChange={setPreviewNiche}
          onLanguageChange={setPreviewLanguage}
          onPreview={handlePreview}
        />
    </div>
  );
}
