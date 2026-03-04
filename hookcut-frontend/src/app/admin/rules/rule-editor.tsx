"use client";

import { useState } from "react";
import {
  BookOpen,
  Trash2,
  Save,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";
import type { PromptRule } from "@/lib/types";

interface RuleEditorProps {
  selectedRule: PromptRule;
  editTitle: string;
  editContent: string;
  editActive: boolean;
  saving: boolean;
  deleting: boolean;
  onEditTitle: (value: string) => void;
  onEditContent: (value: string) => void;
  onEditActive: (value: boolean) => void;
  onSave: () => void;
  onDelete: () => void;
}

export default function RuleEditor({
  selectedRule,
  editTitle,
  editContent,
  editActive,
  saving,
  deleting,
  onEditTitle,
  onEditContent,
  onEditActive,
  onSave,
  onDelete,
}: RuleEditorProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-sm font-semibold text-white/70 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-violet-400" />
          Edit Rule
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/30 font-mono">
            v{selectedRule.version}
          </span>
        </h2>
        {selectedRule.is_base_rule && (
          <span className="text-[10px] px-2.5 py-1 rounded-full bg-violet-500/10 text-violet-300 border border-violet-500/20">
            Base Rule
          </span>
        )}
      </div>

      <div className="space-y-4">
        {/* Title */}
        <div>
          <label className="text-xs font-medium text-white/40 mb-2 block">
            Title
          </label>
          <input
            type="text"
            value={editTitle}
            onChange={(e) => onEditTitle(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm text-white/80 placeholder-white/20 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all"
          />
        </div>

        {/* Content */}
        <div>
          <label className="text-xs font-medium text-white/40 mb-2 block">
            Content
          </label>
          <textarea
            value={editContent}
            onChange={(e) => onEditContent(e.target.value)}
            rows={10}
            className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-sm text-white/80 placeholder-white/20 outline-none focus:border-violet-500/40 focus:ring-1 focus:ring-violet-500/20 transition-all font-mono min-h-[200px] resize-y"
          />
        </div>

        {/* Active toggle */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.05]">
          <span className="text-sm text-white/60">
            Rule Status
          </span>
          <button
            onClick={() => onEditActive(!editActive)}
            className="flex items-center gap-2 text-sm"
          >
            {editActive ? (
              <>
                <ToggleRight className="w-6 h-6 text-emerald-400" />
                <span className="text-emerald-300">Active</span>
              </>
            ) : (
              <>
                <ToggleLeft className="w-6 h-6 text-white/30" />
                <span className="text-white/40">Inactive</span>
              </>
            )}
          </button>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={onSave}
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-500/15 text-violet-300 border border-violet-500/30 hover:bg-violet-500/25 transition-all duration-200 text-sm font-medium disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? "Saving..." : "Save Changes"}
          </button>
          {!selectedRule.is_base_rule && (
            <>
              {confirmDelete ? (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-red-400/70">
                    Confirm delete?
                  </span>
                  <button
                    onClick={() => {
                      onDelete();
                      setConfirmDelete(false);
                    }}
                    disabled={deleting}
                    className="px-3 py-2 rounded-xl text-sm text-red-400 border border-red-500/25 hover:bg-red-500/10 transition-all duration-200 disabled:opacity-50"
                  >
                    {deleting ? "Deleting..." : "Yes, Delete"}
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="px-3 py-2 rounded-xl text-sm text-white/40 hover:text-white/60 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm text-red-400/70 border border-red-500/15 hover:bg-red-500/10 hover:text-red-400 transition-all duration-200"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
