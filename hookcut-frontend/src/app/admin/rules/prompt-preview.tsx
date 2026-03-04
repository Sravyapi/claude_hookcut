"use client";

import { motion } from "framer-motion";
import { Eye } from "lucide-react";
import type { PromptPreview } from "@/lib/types";
import { NICHES } from "@/lib/constants";

const LANGUAGES = [
  "English",
  "Hinglish",
  "Hindi",
  "Tamil",
  "Telugu",
  "Kannada",
  "Malayalam",
  "Marathi",
  "Gujarati",
  "Punjabi",
  "Bengali",
  "Odia",
  "Other",
];

interface PromptPreviewPanelProps {
  previewNiche: string;
  previewLanguage: string;
  preview: PromptPreview | null;
  loadingPreview: boolean;
  onNicheChange: (value: string) => void;
  onLanguageChange: (value: string) => void;
  onPreview: () => void;
}

export default function PromptPreviewPanel({
  previewNiche,
  previewLanguage,
  preview,
  loadingPreview,
  onNicheChange,
  onLanguageChange,
  onPreview,
}: PromptPreviewPanelProps) {
  return (
    <motion.div
      className="mt-6 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 }}
    >
      <div className="flex items-center gap-2 mb-5">
        <Eye className="w-4 h-4 text-violet-400" />
        <h2 className="text-sm font-semibold text-white/70">
          Prompt Preview
        </h2>
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-end gap-4 mb-5">
        {/* Niche selector */}
        <div className="flex-1 w-full sm:w-auto">
          <label className="text-xs font-medium text-white/40 mb-2 block">
            Niche
          </label>
          <select
            value={previewNiche}
            onChange={(e) => onNicheChange(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm text-white/70 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all appearance-none cursor-pointer"
          >
            {NICHES.map((n) => (
              <option key={n} value={n} className="bg-zinc-900 text-white">
                {n}
              </option>
            ))}
          </select>
        </div>

        {/* Language selector */}
        <div className="flex-1 w-full sm:w-auto">
          <label className="text-xs font-medium text-white/40 mb-2 block">
            Language
          </label>
          <select
            value={previewLanguage}
            onChange={(e) => onLanguageChange(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm text-white/70 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all appearance-none cursor-pointer"
          >
            {LANGUAGES.map((l) => (
              <option key={l} value={l} className="bg-zinc-900 text-white">
                {l}
              </option>
            ))}
          </select>
        </div>

        {/* Preview button */}
        <button
          onClick={onPreview}
          disabled={loadingPreview}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-500/15 text-violet-300 border border-violet-500/30 hover:bg-violet-500/25 transition-all duration-200 text-sm font-medium disabled:opacity-50 shrink-0"
        >
          <Eye className="w-4 h-4" />
          {loadingPreview ? "Loading..." : "Preview Prompt"}
        </button>
      </div>

      {/* Preview output */}
      {preview && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div className="flex items-center gap-4 mb-3">
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-white/5 text-white/40 border border-white/[0.06]">
              {preview.rule_count} rules
            </span>
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-white/5 text-white/40 border border-white/[0.06]">
              {preview.character_count.toLocaleString()} characters
            </span>
          </div>
          <pre className="bg-black/30 rounded-lg p-4 text-xs font-mono overflow-x-auto max-h-96 overflow-y-auto text-white/60 whitespace-pre-wrap break-words leading-relaxed">
            {preview.prompt_text}
          </pre>
        </motion.div>
      )}

      {!preview && !loadingPreview && (
        <p className="text-xs text-white/25 text-center py-4">
          Select a niche and language, then click &quot;Preview Prompt&quot;
          to see the assembled prompt
        </p>
      )}
    </motion.div>
  );
}
