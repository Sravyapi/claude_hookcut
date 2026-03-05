export default function Loading() {
  return (
    <div className="min-h-screen bg-[#FAFAF8] flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="w-7 h-7 rounded-full border-2 border-[#E4E4E7] border-t-[#E84A2F] animate-spin" />
        <p className="text-[#A1A1AA] text-sm">Loading\u2026</p>
      </div>
    </div>
  );
}
