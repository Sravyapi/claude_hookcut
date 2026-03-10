"use client";

type AspectRatioPickerProps = {
  value: "9:16" | "1:1" | "4:5";
  onChange: (value: "9:16" | "1:1" | "4:5") => void;
};

const RATIOS = [
  { value: "9:16" as const, label: "9:16", sublabel: "Shorts / TikTok", w: 18, h: 32 },
  { value: "1:1" as const, label: "1:1", sublabel: "Instagram / X", w: 24, h: 24 },
  { value: "4:5" as const, label: "4:5", sublabel: "Instagram / FB", w: 20, h: 25 },
];

export function AspectRatioPicker({ value, onChange }: AspectRatioPickerProps) {
  return (
    <div className="flex gap-3">
      {RATIOS.map(ratio => (
        <button
          key={ratio.value}
          onClick={() => onChange(ratio.value)}
          className={`flex-1 flex flex-col items-center gap-2 py-3 px-2 rounded-xl transition-colors ${
            value === ratio.value
              ? "bg-violet-500/15 border border-violet-500/30 text-violet-300"
              : "bg-white/5 border border-white/5 text-white/50 hover:bg-white/10"
          }`}
        >
          {/* Visual ratio shape */}
          <div
            className={`rounded-sm border-2 ${
              value === ratio.value ? "border-violet-400" : "border-white/20"
            }`}
            style={{ width: ratio.w, height: ratio.h }}
          />
          <span className="text-xs font-medium">{ratio.label}</span>
          <span className="text-[10px] opacity-60">{ratio.sublabel}</span>
        </button>
      ))}
    </div>
  );
}
