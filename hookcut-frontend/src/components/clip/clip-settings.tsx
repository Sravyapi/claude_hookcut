"use client";

import type { CaptionStyle } from "@/lib/types";
import { AspectRatioPicker } from "@/components/shared/aspect-ratio-picker";

type ClipSettingsData = {
  aspectRatio: "9:16" | "1:1" | "4:5";
  captionStyle: CaptionStyle;
  captionsEnabled: boolean;
  audioNormalization: boolean;
};

type ClipSettingsProps = {
  settings: ClipSettingsData;
  onUpdate: (changes: Partial<ClipSettingsData>) => void;
};

const CAPTION_STYLES: { value: CaptionStyle; label: string }[] = [
  { value: "clean", label: "Clean" },
  { value: "bold", label: "Bold" },
  { value: "neon", label: "Neon" },
  { value: "minimal", label: "Minimal" },
];

export function ClipSettings({ settings, onUpdate }: ClipSettingsProps) {
  return (
    <div className="glass-card p-6 rounded-2xl space-y-5">
      <h3 className="text-lg font-semibold text-white">Settings</h3>

      {/* Aspect Ratio */}
      <div>
        <label className="block text-sm text-white/60 mb-2">Aspect Ratio</label>
        <AspectRatioPicker
          value={settings.aspectRatio}
          onChange={v => onUpdate({ aspectRatio: v })}
        />
      </div>

      {/* Caption Style */}
      <div>
        <label className="block text-sm text-white/60 mb-2">Caption Style</label>
        <div className="grid grid-cols-4 gap-2">
          {CAPTION_STYLES.map(style => (
            <button
              key={style.value}
              onClick={() => onUpdate({ captionStyle: style.value })}
              className={`py-2 rounded-lg text-sm font-medium transition-colors ${
                settings.captionStyle === style.value
                  ? "bg-violet-500/20 text-violet-300 border border-violet-500/30"
                  : "bg-white/5 text-white/60 border border-white/5 hover:bg-white/10"
              }`}
            >
              {style.label}
            </button>
          ))}
        </div>
      </div>

      {/* Toggles */}
      <div className="space-y-3">
        <label className="flex items-center justify-between cursor-pointer">
          <span className="text-sm text-white/70">Captions</span>
          <button
            role="switch"
            aria-checked={settings.captionsEnabled}
            onClick={() => onUpdate({ captionsEnabled: !settings.captionsEnabled })}
            className={`relative w-10 h-5 rounded-full transition-colors ${
              settings.captionsEnabled ? "bg-violet-500" : "bg-white/10"
            }`}
          >
            <div
              className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                settings.captionsEnabled ? "translate-x-5" : ""
              }`}
            />
          </button>
        </label>

        <label className="flex items-center justify-between cursor-pointer">
          <span className="text-sm text-white/70">Audio Normalization</span>
          <button
            role="switch"
            aria-checked={settings.audioNormalization}
            onClick={() => onUpdate({ audioNormalization: !settings.audioNormalization })}
            className={`relative w-10 h-5 rounded-full transition-colors ${
              settings.audioNormalization ? "bg-violet-500" : "bg-white/10"
            }`}
          >
            <div
              className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                settings.audioNormalization ? "translate-x-5" : ""
              }`}
            />
          </button>
        </label>
      </div>
    </div>
  );
}
