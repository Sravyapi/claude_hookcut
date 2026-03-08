export default function Loading() {
  return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center px-6">
      <div
        className="flex flex-col items-center gap-5 rounded-2xl px-10 py-10"
        style={{
          background: "rgba(255,255,255,0.03)",
          border: "1px solid rgba(255,255,255,0.07)",
          backdropFilter: "blur(12px)",
        }}
      >
        {/* Spinner — brand color */}
        <div className="relative w-10 h-10">
          <div className="w-10 h-10 rounded-full border-2 border-white/[0.08] border-t-[#E84A2F] animate-spin" />
        </div>

        {/* Label */}
        <div className="flex flex-col items-center gap-1 text-center">
          <p className="text-white/70 text-sm font-medium">Loading HookCut</p>
          <p className="text-white/25 text-xs font-mono">Preparing your workspace…</p>
        </div>
      </div>
    </div>
  );
}
