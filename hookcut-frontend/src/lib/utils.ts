import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes with clsx — required by shadcn/ui components */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** Score color tier: returns hex color for SVG and Tailwind classes for bars/dots. */
export function getScoreColor(value: number): {
  hex: string;
  gradient: string;
  dot: string;
} {
  if (value >= 8)
    return { hex: "#34d399", gradient: "from-emerald-500 to-emerald-400", dot: "bg-emerald-400" };
  if (value >= 6)
    return { hex: "#a78bfa", gradient: "from-violet-500 to-violet-400", dot: "bg-violet-400" };
  if (value >= 4)
    return { hex: "#fbbf24", gradient: "from-amber-500 to-amber-400", dot: "bg-amber-400" };
  return { hex: "#f87171", gradient: "from-red-500 to-red-400", dot: "bg-red-400" };
}

export function youtubeThumbUrl(videoId: string): string {
  return `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
}
