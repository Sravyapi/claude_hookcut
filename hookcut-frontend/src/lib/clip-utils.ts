/**
 * Format seconds as m:ss.s (e.g., 1:23.5)
 */
export function formatClipTime(seconds: number): string {
  const safe = Math.max(0, seconds);
  const m = Math.floor(safe / 60);
  const s = (safe % 60).toFixed(1);
  return `${m}:${s.padStart(4, "0")}`;
}
