"use client";

import { memo } from "react";

interface ClipFormProps {
  url: string;
  onUrlChange: (url: string) => void;
  onSubmit: () => void;
}

export const ClipForm = memo(function ClipForm({ url, onUrlChange, onSubmit }: ClipFormProps) {
  return (
    <div className="glass-card p-6 rounded-2xl">
      <label className="block text-sm text-white/60 mb-2">YouTube URL</label>
      <div className="flex gap-3">
        <input
          type="url"
          value={url}
          onChange={e => onUrlChange(e.target.value)}
          onKeyDown={e => e.key === "Enter" && onSubmit()}
          placeholder="https://www.youtube.com/watch?v=..."
          className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:border-violet-500/50"
        />
        <button
          type="button"
          onClick={onSubmit}
          disabled={!url}
          className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Load Video
        </button>
      </div>
    </div>
  );
});
