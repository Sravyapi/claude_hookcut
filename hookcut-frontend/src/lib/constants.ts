// ─── Runtime Constants ───
// Moved from types.ts to keep type-only definitions separate from values.

export const MAX_SELECTED_HOOKS = 3;

export const NICHES = [
  "Tech / AI",
  "Finance",
  "Fitness",
  "Relationships",
  "Drama / Commentary",
  "Entrepreneurship",
  "Podcast",
  "Generic",
] as const;

export const HOOK_TYPE_COLORS: Record<string, string> = {
  "Curiosity Gap": "bg-purple-500/20 text-purple-300 border-purple-500/30",
  "Direct Benefit": "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  "Fear-Based": "bg-red-500/20 text-red-300 border-red-500/30",
  Authority: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  Contrarian: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  Counterintuitive: "bg-pink-500/20 text-pink-300 border-pink-500/30",
  "Story-Based": "bg-amber-500/20 text-amber-300 border-amber-500/30",
  "Pattern Interrupt": "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
  "High Stakes Warning": "bg-rose-500/20 text-rose-300 border-rose-500/30",
  "Social Proof": "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
  Elimination: "bg-slate-500/20 text-slate-300 border-slate-500/30",
  "Objection Handler": "bg-teal-500/20 text-teal-300 border-teal-500/30",
  "Pain Escalation": "bg-rose-600/20 text-rose-300 border-rose-600/30",
  "Personal Transformation": "bg-violet-500/20 text-violet-300 border-violet-500/30",
  "Live Proof": "bg-lime-500/20 text-lime-300 border-lime-500/30",
  "FOMO Setup": "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  "Zero-Second Claim": "bg-fuchsia-500/20 text-fuchsia-300 border-fuchsia-500/30",
  "Extended Demo": "bg-sky-500/20 text-sky-300 border-sky-500/30",
};

export const FUNNEL_ROLE_LABELS: Record<string, string> = {
  curiosity_opener: "Curiosity Opener",
  pain_escalation: "Pain Escalation",
  solution_reveal: "Solution Reveal",
  proof_authority: "Proof / Authority",
  retention_hook: "Retention Hook",
  extended_demo: "Extended Demo",
};

export const HOOK_TYPE_DESCRIPTIONS: Record<string, string> = {
  "Curiosity Gap": "Creates an unresolved question the viewer must stay to answer",
  "Direct Benefit": "Promises a clear, tangible outcome the viewer wants",
  "Fear-Based": "Triggers loss aversion — what they'll miss or lose",
  Authority: "Leverages credentials or expertise to build instant trust",
  Contrarian: "Challenges conventional wisdom to provoke engagement",
  Counterintuitive: "Presents a surprising claim that defies expectations",
  "Story-Based": "Opens a narrative arc the viewer needs to see resolved",
  "Pattern Interrupt": "Breaks the scroll pattern with something unexpected",
  "High Stakes Warning": "Signals urgent consequences of inaction",
  "Social Proof": "Uses others' results or popularity to validate the message",
  Elimination: "Systematically removes expected answers, building suspense",
  "Objection Handler": "Catches viewers at the moment they'd normally bounce",
  "Pain Escalation": "Layers frustration to make the solution feel urgent",
  "Personal Transformation": "Shows a before/after journey viewers aspire to",
  "Live Proof": "Demonstrates results in real-time for instant credibility",
  "FOMO Setup": "Creates fear of missing exclusive or time-limited value",
  "Zero-Second Claim": "Opens with a bold, attention-grabbing statement immediately",
  "Extended Demo": "Walks through a complete process, building investment step by step",
};

export const PAYG_OPTIONS = [100, 200, 500, 1000] as const;

export function getStatusConfig(status: string): { label: string; color: string } {
  switch (status) {
    case "pending":
      return { label: "Pending", color: "bg-yellow-500/20 text-yellow-400" };
    case "analyzing":
      return { label: "Analyzing", color: "bg-blue-500/20 text-blue-400" };
    case "hooks_ready":
      return { label: "Hooks Ready", color: "bg-green-500/20 text-green-400" };
    case "generating_shorts":
      return { label: "Generating", color: "bg-purple-500/20 text-purple-400" };
    case "completed":
      return { label: "Completed", color: "bg-emerald-500/20 text-emerald-400" };
    case "failed":
      return { label: "Failed", color: "bg-red-500/20 text-red-400" };
    default:
      return { label: status, color: "bg-gray-500/20 text-gray-400" };
  }
}
