import { useState, useCallback, useRef } from "react";

// ═══════════════════════════════════════════════════════
// HOOKCUT v4 — PRD v3 ALIGNED
// NyxPath AI Labs • hook_engine_v4
//
// Architecture: Pure LLM, no pre-filtering
// Scoring: LLM holistic (no fixed weights)
// Niches: 8 (PRD v3 canonical)
// Hook types: 13 (PRD v3 canonical)
// Funnel roles: 6
// Learned rules: 17 (A–Q)
// Mode: V0 (dev) — timestamps visible
// ═══════════════════════════════════════════════════════

// ───────────────────────────────────────────────────────
// LANGUAGE CONFIG
// ───────────────────────────────────────────────────────
const LANGUAGES = {
  "English": {
    label: "English",
    promptNote: "LANGUAGE: English (possibly Indian English with Hinglish code-switching). Hindi words mixed into English are acceptable — do not reject hooks for code-switching.",
  },
  "Hinglish": {
    label: "Hinglish (Hindi + English)",
    promptNote: "LANGUAGE: Hinglish — a natural mix of Hindi and English common among Indian creators. Both languages flow within sentences. Output hook_text in the ORIGINAL mixed language exactly as spoken — NEVER normalize to pure English or pure Hindi.",
  },
  "Hindi": {
    label: "Hindi (हिन्दी)",
    promptNote: "LANGUAGE: Hindi (Devanagari or romanized). Code-switching to English for technical terms is normal. Output hook_text in the ORIGINAL Hindi — NEVER translate.",
  },
  "Tamil": {
    label: "Tamil (தமிழ்)",
    promptNote: "LANGUAGE: Tamil (or Tanglish — Tamil mixed with English). Code-switching to English is very common among Tamil tech/education creators. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
  "Telugu": {
    label: "Telugu (తెలుగు)",
    promptNote: "LANGUAGE: Telugu (or Telugu mixed with English). Code-switching to English for technical terms is very common. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
  "Kannada": {
    label: "Kannada (ಕನ್ನಡ)",
    promptNote: "LANGUAGE: Kannada (or Kannada mixed with English). Code-switching is common. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
  "Malayalam": {
    label: "Malayalam (മലയാളം)",
    promptNote: "LANGUAGE: Malayalam (or Manglish — Malayalam mixed with English). Code-switching is common. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
  "Marathi": {
    label: "Marathi (मराठी)",
    promptNote: "LANGUAGE: Marathi (or Marathi mixed with English/Hindi). Code-switching is common. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
  "Gujarati": {
    label: "Gujarati (ગુજરાતી)",
    promptNote: "LANGUAGE: Gujarati (or Gujarati mixed with English/Hindi). Code-switching is common especially in business/finance content. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
  "Punjabi": {
    label: "Punjabi (ਪੰਜਾਬੀ)",
    promptNote: "LANGUAGE: Punjabi (Gurmukhi or romanized, or Punjabi mixed with English/Hindi). Code-switching is common. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
  "Bengali": {
    label: "Bengali (বাংলা)",
    promptNote: "LANGUAGE: Bengali (or Banglish — Bengali mixed with English). Code-switching is common. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
  "Odia": {
    label: "Odia (ଓଡ଼ିଆ)",
    promptNote: "LANGUAGE: Odia (or Odia mixed with English/Hindi). Code-switching is common. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
  "Other": {
    label: "Other Language",
    promptNote: "LANGUAGE: Auto-detect from transcript. Code-switching to English or Hindi is normal for Indian creators. Apply all hook rules identically. Output hook_text in the ORIGINAL language — NEVER translate.",
  },
};

// ───────────────────────────────────────────────────────
// NICHE / AUDIENCE CONFIG (PRD v3 Section 04)
// ───────────────────────────────────────────────────────
const NICHES = {
  "Tech / AI": {
    softRange: "12–30s",
    stakes: "Disruption, obsolescence, breakthrough capability, competitive advantage, AI replacing humans, paradigm shifts",
    tone: "Bold, precise, forward-looking. Clear insight or surprising claim about technology impact.",
    preferredTypes: ["Zero-Second Claim", "Insight Reveal", "Counterintuitive", "High Stakes Warning", "Live Proof"],
  },
  "Finance": {
    softRange: "15–35s",
    stakes: "Money lost/gained, hidden risk, wealth gap, market timing, financial ruin, generational wealth",
    tone: "Risk/reward framing. Concrete numbers, specific dollar figures, market-moving events.",
    preferredTypes: ["Fear-Based", "High Stakes Warning", "Direct Benefit", "Contrarian", "FOMO Setup"],
  },
  "Fitness": {
    softRange: "10–25s",
    stakes: "Wasted effort, transformation, body image, injury risk, health, discipline, myth-busting",
    tone: "Clear result or myth-busting. Proof something works or they're doing it wrong.",
    preferredTypes: ["Contrarian", "Direct Benefit", "Personal Transformation", "Counterintuitive"],
  },
  "Relationships": {
    softRange: "10–25s",
    stakes: "Emotional pain, betrayal, vulnerability, connection, toxic patterns, self-sabotage",
    tone: "Emotional tension. Raw honesty and personal stakes feel authentic.",
    preferredTypes: ["Story-Based", "Pattern Interrupt", "Curiosity Gap", "Personal Transformation"],
  },
  "Drama / Commentary": {
    softRange: "12–30s",
    stakes: "Conflict, controversy, hypocrisy, public exposure, power dynamics, hidden motives, call-out",
    tone: "Conflict or controversy. Viewers want to pick a side immediately.",
    preferredTypes: ["Pattern Interrupt", "High Stakes Warning", "Zero-Second Claim", "Fear-Based"],
  },
  "Entrepreneurship": {
    softRange: "15–30s",
    stakes: "Business failure, hard-earned lessons, missed opportunity, scaling pain, costly mistakes, status, money left on table",
    tone: "Hard-earned insight or costly mistake. Authenticity and specificity beat generic advice.",
    preferredTypes: ["Story-Based", "High Stakes Warning", "Insight Reveal", "Contrarian", "Personal Transformation"],
  },
  "Podcast": {
    softRange: "15–40s",
    stakes: "Insight reveal, surprising reframe, expert credibility, insider access, counterintuitive wisdom",
    tone: "Deep insight or surprising reframe from an expert. The viewer should feel they're hearing something they wouldn't get elsewhere.",
    preferredTypes: ["Insight Reveal", "Counterintuitive", "Authority", "Story-Based", "Curiosity Gap"],
  },
  "Generic": {
    softRange: "12–30s",
    stakes: "Broad curiosity gap, universal emotion, surprising claim, unexpected fact",
    tone: "Surprising, specific, and emotionally resonant. Works for any audience.",
    preferredTypes: ["Curiosity Gap", "Counterintuitive", "Direct Benefit", "Story-Based"],
  },
};

// PRD v3 canonical 13 hook types
const HOOK_TYPES = [
  "Curiosity Gap", "Direct Benefit", "Fear-Based", "Authority", "Contrarian",
  "Counterintuitive", "Story-Based", "Pattern Interrupt", "High Stakes Warning",
  "Social Proof", "Personal Transformation", "Live Proof", "FOMO Setup",
  "Zero-Second Claim", "Extended Demo",
];

// 6 funnel roles
const FUNNEL_ROLES = [
  "curiosity_opener", "pain_escalation", "solution_reveal",
  "proof_authority", "retention_hook", "extended_demo",
];

const SAMPLE_TRANSCRIPT = `[0:00] So here's the thing about AI that nobody is talking about.
[0:04] In the next 18 months, 40% of all entry-level coding jobs will be automated.
[0:09] Not maybe. Not possibly. This is already happening at companies like Google and Meta.
[0:14] I talked to a VP at one of these companies last week and he told me something that genuinely scared me.
[0:19] They've already reduced their junior hiring by 30% this year alone.
[0:23] And it's not because the economy is bad. It's because AI can now do what a junior developer does in a tenth of the time.
[0:30] Now before you panic, there's actually a massive opportunity here.
[0:34] The people who understand how to work WITH AI, not against it, are getting promoted faster than ever.
[0:40] I went from making 80K to 220K in two years by learning exactly three skills.
[0:46] And none of them are what you'd expect.
[0:48] The first one is what I call prompt architecture.
[0:51] It's not prompt engineering. That's already becoming commoditized.
[0:55] Prompt architecture is about designing systems where AI does 80% of the work and you do the critical 20%.
[1:01] Let me show you exactly how I set this up at my company.
[1:05] So step one is understanding the limitation of current models.
[1:09] Most people think ChatGPT can do everything. They're wrong.
[1:13] It's great at about 7 things and terrible at about 50 things.
[1:17] And if you don't know the difference, you'll waste months building the wrong thing.
[1:22] The second skill — and this is the one that tripled my salary — is what I call AI-augmented decision making.
[1:28] Basically, you use AI to generate 50 options in 10 minutes, then you use human judgment to pick the right one.
[1:35] Nobody else in my team was doing this. They were either fully manual or fully automated.
[1:40] I was the only one in the middle. And that's where all the leverage is.
[1:45] Make sure to like and subscribe if you want more content like this.`;

// ───────────────────────────────────────────────────────
// LLM PROMPT — 5-LAYER EVALUATION STACK + 17 RULES
// ───────────────────────────────────────────────────────
function buildPrompt(niche, transcript, language = "English") {
  const n = NICHES[niche];
  const lang = LANGUAGES[language] || LANGUAGES["English"];
  return `You are a hook evaluator for YouTube Shorts. Extract the 5 best hook segments from this transcript.

NICHE: ${niche} | DURATION: ${n.softRange} | STAKES: ${n.stakes} | TONE: ${n.tone}
PREFERRED TYPES: ${n.preferredTypes.join(", ")}
${lang.promptNote}

FILLER DETECTION (contextual, any language): Exclude channel greetings, verbal stalling, subscribe/like/share CTAs, section navigation phrases, and filler affirmations. Indian references (lakhs, crores, UPSC, IIT, UPI) are valid signals — never filter.

SIGNAL PATTERNS TO HUNT:
Tier 1 (STRONGEST): Zero-second high-stakes claims (shocking numbers, corporate war) | Live proof demos ("watch this") | Free/unfair advantage reveals | FOMO/exclusivity ("99% don't know") | Empathy+solution ("if you're ambitious but lazy...") | Named framework reveals ("The GPS Method")
Tier 2 (STRONG): Specific numbers | Contrarian framing | Emotional spikes | Personal transformation | Old-vs-new contrasts | Objection handling | Uncomfortable truths (harsh reality, calm tone) | Behind-the-scenes ROI (personal financial numbers) | Relatable hot takes (permission to be different) | Incomplete lists ("17 habits") | Credibility+vulnerability combo | Systems-over-willpower framing | Myth-busting ("to-do lists are ruining your life") | Paradigm shift promises ("firmware update for your brain") | Life-changing moment stories ("exact moment that changed my life") | Framework cliffhangers
Tier 3 (ENHANCEMENT): Vivid analogies | Immersive "you" framing | Rapid-fire escalation
NO ENERGY BIAS: Calm structured delivery = equally hookable as high-energy. Judge by content structure, not delivery energy.

BOUNDARY RULES:
- Start at complete sentence beginning, end at sentence boundary or open loop
- STANDALONE TEST: stranger reads with zero context and must NOT say "what came before this?"
- Never start with filler, section labels, or CTA language
- End at PEAK TENSION. All 5 hooks must have non-overlapping timestamps.
- Extended demos can run 30-50s if each step escalates

17 RULES (A-Q):
A. One topic per hook — 3+ topics = FAIL
B. Contextual grounding — viewer must know WHO and WHY immediately
C. Specificity serves one point only
D. Character + proof arc (person + achievement in tight sequence)
E. Let hook breathe — include follow-up sentences that complete the thought
F. Urgency/FOMO framing ("while you were sleeping...")
G. No generic claims without specific proof
H. Narrative escalation: intrigue→proof→escalation→contrast→open loop
I. Composite hooks: stitch non-contiguous segments for stronger arcs (mark as "X:XX+Y:YY [composite]")
J. End at the landing — not before, not after
K. Unresolved mechanism: viewer knows WHAT not HOW
L. Pain escalation: layer frustration (statement→specifics→vivid analogy)
M. Elimination hooks: remove expected answers systematically
N. Objection handling: catch viewers at bounce moment
O. Funnel role diversity: 5 hooks serve different purposes
P. Strip section labels/navigation text from hook starts
Q. Workflow demos: include full step-by-step sequence, don't cut mid-demo

SCORING (7 dimensions, 0-10, holistic):
scroll_stop | curiosity_gap | stakes_intensity | emotional_voltage | standalone_clarity | thematic_focus (GATING: <5 = not top 3) | thought_completeness (cuts early ≤4, past landing ≤5, delivers value while withholding = 8+)
attention_score: YOUR independent editorial judgment (0-10), NOT a formula.

CLASSIFY each hook:
TYPE: Curiosity Gap|Direct Benefit|Fear-Based|Authority|Contrarian|Counterintuitive|Story-Based|Pattern Interrupt|High Stakes Warning|Social Proof|Personal Transformation|Live Proof|FOMO Setup|Zero-Second Claim|Extended Demo
FUNNEL ROLE: curiosity_opener|pain_escalation|solution_reveal|proof_authority|retention_hook|extended_demo

OUTPUT: Return ONLY valid JSON, no markdown. EXACTLY 5 hooks. Keep explanations CONCISE (under 30 words each).
{
  "hooks": [{
    "rank": 1,
    "hook_text": "EXACT verbatim transcript text",
    "start_time": "M:SS",
    "end_time": "M:SS",
    "hook_type": "primary type",
    "funnel_role": "role",
    "scores": {"scroll_stop":0,"curiosity_gap":0,"stakes_intensity":0,"emotional_voltage":0,"standalone_clarity":0,"thematic_focus":0,"thought_completeness":0},
    "attention_score": 0.0,
    "platform_dynamics": "Under 30 words: pattern interrupt + open loop + algorithm boost",
    "viewer_psychology": "Under 30 words: curiosity gap + tension + grounding"
  }]
}

TRANSCRIPT:
${transcript}`;
}

// ───────────────────────────────────────────────────────
// UI COMPONENTS
// ───────────────────────────────────────────────────────

const TYPE_COLORS = {
  "Curiosity Gap": "#f59e0b", "Direct Benefit": "#22c55e", "Fear-Based": "#ef4444",
  "Authority": "#3b82f6", "Contrarian": "#a855f7", "Counterintuitive": "#ec4899",
  "Story-Based": "#06b6d4", "Pattern Interrupt": "#f97316", "High Stakes Warning": "#ff6b35",
  "Social Proof": "#10b981", "Personal Transformation": "#8b5cf6", "Live Proof": "#14b8a6",
  "FOMO Setup": "#fbbf24", "Zero-Second Claim": "#dc2626", "Extended Demo": "#0ea5e9",
};

const ROLE_STYLES = {
  curiosity_opener: { bg: "#f59e0b12", fg: "#f59e0b", border: "#f59e0b22" },
  pain_escalation: { bg: "#ef444412", fg: "#ef4444", border: "#ef444422" },
  solution_reveal: { bg: "#22c55e12", fg: "#22c55e", border: "#22c55e22" },
  proof_authority: { bg: "#3b82f612", fg: "#3b82f6", border: "#3b82f622" },
  retention_hook: { bg: "#a855f712", fg: "#a855f7", border: "#a855f722" },
  extended_demo: { bg: "#06b6d412", fg: "#06b6d4", border: "#06b6d422" },
};

const RANK_COLORS = ["#ff6b35", "#3b82f6", "#a855f7", "#06b6d4", "#6b6b80"];
const SCORE_DEFS = [
  { key: "scroll_stop", label: "Scroll Stop", color: "#ff6b35" },
  { key: "curiosity_gap", label: "Curiosity", color: "#f59e0b" },
  { key: "stakes_intensity", label: "Stakes", color: "#ef4444" },
  { key: "emotional_voltage", label: "Emotion", color: "#ec4899" },
  { key: "standalone_clarity", label: "Standalone", color: "#3b82f6" },
  { key: "thematic_focus", label: "Focus", color: "#a855f7" },
  { key: "thought_completeness", label: "Completeness", color: "#06b6d4" },
];

function attnColor(v) {
  if (v >= 8.5) return "#22c55e";
  if (v >= 7.0) return "#3b82f6";
  if (v >= 5.5) return "#f59e0b";
  return "#ef4444";
}

function ScoreBar({ label, value, color }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ width: 78, color: "#5a5a72", flexShrink: 0, fontSize: 10, fontWeight: 500 }}>{label}</span>
      <div style={{ flex: 1, height: 4, background: "#14141e", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: `${Math.min(value * 10, 100)}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.6s ease" }} />
      </div>
      <span style={{ width: 24, textAlign: "right", fontFamily: "var(--mono)", fontWeight: 600, color, fontSize: 10 }}>{value.toFixed(1)}</span>
    </div>
  );
}

function DnaBlock({ title, icon, color, items }) {
  const valid = items.filter(([, v]) => v);
  if (!valid.length) return null;
  return (
    <div style={{ padding: "10px 12px", background: color + "08", borderRadius: 8, border: `1px solid ${color}12` }}>
      <div style={{ fontSize: 9, fontWeight: 700, color, textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 6 }}>{icon} {title}</div>
      {valid.map(([k, v]) => (
        <div key={k} style={{ marginBottom: 4, lineHeight: 1.55 }}>
          <span style={{ fontSize: 10, fontWeight: 600, color: color + "aa" }}>{k}: </span>
          <span style={{ fontSize: 11, color: "#b8b8cc" }}>{v}</span>
        </div>
      ))}
    </div>
  );
}

function HookCard({ hook, index, verdict, onVerdict, fb, onFb }) {
  const [showDna, setShowDna] = useState(false);
  const tc = TYPE_COLORS[hook.hook_type] || "#ff6b35";
  const attn = hook.attention_score ?? 0;
  const sc = hook.scores ?? {};
  const pd = hook.platform_dynamics || hook.explanation?.platform_dynamics || "";
  const vp = hook.viewer_psychology || hook.explanation?.viewer_psychology || "";
  const rs = ROLE_STYLES[hook.funnel_role] || ROLE_STYLES.curiosity_opener;
  const isApp = verdict === "approve", isRej = verdict === "reject";
  const isComposite = hook.start_time?.includes("+") || hook.start_time?.includes("composite");

  return (
    <div style={{
      background: isApp ? "#22c55e05" : isRej ? "#ef444405" : "#0d0d16",
      border: isApp ? "1.5px solid #22c55e35" : isRej ? "1.5px solid #ef444420" : "1px solid #1c1c2c",
      borderRadius: 10, overflow: "hidden", transition: "all 0.15s",
    }}>
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "9px 12px", borderBottom: `1px solid ${isApp ? "#22c55e10" : isRej ? "#ef44440a" : "#161622"}`, flexWrap: "wrap" }}>
        <div style={{
          width: 24, height: 24, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center",
          background: RANK_COLORS[index], fontSize: 11, fontWeight: 700, color: "#fff", flexShrink: 0,
        }}>{index + 1}</div>

        {/* hook type pill */}
        <span style={{ padding: "2px 8px", borderRadius: 10, fontSize: 10, fontWeight: 600, background: tc + "15", color: tc, border: `1px solid ${tc}25` }}>{hook.hook_type}</span>

        {/* funnel role */}
        {hook.funnel_role && (
          <span style={{ padding: "2px 6px", borderRadius: 6, fontSize: 9, fontWeight: 600, background: rs.bg, color: rs.fg, border: `1px solid ${rs.border}` }}>
            {hook.funnel_role.replace(/_/g, " ")}
          </span>
        )}

        {/* composite badge */}
        {isComposite && (
          <span style={{ padding: "1px 5px", borderRadius: 5, fontSize: 8, background: "#fbbf2415", color: "#fbbf24", border: "1px solid #fbbf2425", fontWeight: 700 }}>COMPOSITE</span>
        )}

        <div style={{ flex: 1 }} />

        {/* attention score */}
        <span style={{
          padding: "3px 9px", borderRadius: 10, fontFamily: "var(--mono)",
          fontSize: 14, fontWeight: 700, color: attnColor(attn), background: attnColor(attn) + "10",
        }}>
          {attn.toFixed(1)}
        </span>

        {/* V0: timestamps visible for dev verification (PRD v3 Section 06) */}
        <span style={{ fontFamily: "var(--mono)", fontSize: 10, color: "#ff6b35aa" }}>
          {hook.start_time}→{hook.end_time}
        </span>
      </div>

      <div style={{ padding: "10px 12px" }}>
        {/* Hook text */}
        <div style={{
          fontSize: 13, lineHeight: 1.8, color: "#e0e0f0", fontWeight: 500,
          padding: "12px 14px", background: "#0a0a12", borderRadius: 7,
          borderLeft: `3px solid ${tc}`, marginBottom: 10,
        }}>"{hook.hook_text}"</div>

        {/* 7 score bars */}
        <div style={{ display: "flex", flexDirection: "column", gap: 2, marginBottom: 10 }}>
          {SCORE_DEFS.map(d => <ScoreBar key={d.key} label={d.label} value={sc[d.key] ?? 0} color={d.color} />)}
        </div>

        {/* Approve / Reject */}
        <div style={{ display: "flex", gap: 6, marginBottom: 7 }}>
          <button onClick={() => onVerdict(index, isApp ? null : "approve")} style={{
            flex: 1, padding: "7px 0", borderRadius: 6, fontSize: 11, fontWeight: 600,
            fontFamily: "inherit", cursor: "pointer", transition: "all 0.12s",
            background: isApp ? "#22c55e" : "#0a0a12", color: isApp ? "#fff" : "#22c55e",
            border: `1.5px solid ${isApp ? "#22c55e" : "#22c55e30"}`,
          }}>{isApp ? "✓ Approved" : "✓ Approve"}</button>
          <button onClick={() => onVerdict(index, isRej ? null : "reject")} style={{
            flex: 1, padding: "7px 0", borderRadius: 6, fontSize: 11, fontWeight: 600,
            fontFamily: "inherit", cursor: "pointer", transition: "all 0.12s",
            background: isRej ? "#ef4444" : "#0a0a12", color: isRej ? "#fff" : "#ef4444",
            border: `1.5px solid ${isRej ? "#ef4444" : "#ef444430"}`,
          }}>{isRej ? "✗ Rejected" : "✗ Reject"}</button>
        </div>

        <input type="text" placeholder="Feedback (optional)…" value={fb || ""} onChange={e => onFb(index, e.target.value)}
          style={{ width: "100%", padding: "6px 10px", background: "#08080e", color: "#e0e0f0", border: "1px solid #1c1c2c", borderRadius: 5, fontSize: 10, fontFamily: "inherit", outline: "none", boxSizing: "border-box" }}
        />

        {/* DNA toggle */}
        <button onClick={() => setShowDna(!showDna)} style={{ background: "none", border: "none", color: "#4a4a60", fontSize: 10, cursor: "pointer", fontFamily: "inherit", padding: "7px 0 0" }}>
          {showDna ? "▾ Hide" : "▸ Show"} why it works
        </button>

        {showDna && (
          <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 7 }}>
            {typeof pd === "string" ? (
              <>
                {pd && <div style={{ padding: "8px 10px", background: "#22c55e08", borderRadius: 6, border: "1px solid #22c55e12" }}>
                  <div style={{ fontSize: 9, fontWeight: 700, color: "#22c55e", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 4 }}>🎯 Platform Dynamics</div>
                  <div style={{ fontSize: 11, color: "#b8b8cc", lineHeight: 1.6 }}>{pd}</div>
                </div>}
                {vp && <div style={{ padding: "8px 10px", background: "#3b82f608", borderRadius: 6, border: "1px solid #3b82f612" }}>
                  <div style={{ fontSize: 9, fontWeight: 700, color: "#3b82f6", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 4 }}>🧠 Viewer Psychology</div>
                  <div style={{ fontSize: 11, color: "#b8b8cc", lineHeight: 1.6 }}>{vp}</div>
                </div>}
              </>
            ) : (
              <>
                <DnaBlock title="Platform Algorithm Dynamics" icon="🎯" color="#22c55e" items={[
                  ["Pattern Interrupt", pd.pattern_interrupt], ["Open Loop", pd.open_loop],
                  ["Algorithmic Advantage", pd.algorithmic_advantage], ["Implied Authority", pd.implied_authority],
                ]} />
                <DnaBlock title="Viewer Psychology" icon="🧠" color="#3b82f6" items={[
                  ["Curiosity Gap", vp.curiosity_gap], ["Social Tension", vp.social_tension],
                  ["Conflict Bias", vp.conflict_bias], ["Insider Framing", vp.insider_framing],
                  ["Contextual Grounding", vp.contextual_grounding],
                ]} />
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────
// MAIN APP
// ───────────────────────────────────────────────────────
export default function HookCutV4() {
  const [transcript, setTranscript] = useState("");
  const [niche, setNiche] = useState("Tech / AI");
  const [language, setLanguage] = useState("English");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hooks, setHooks] = useState(null);
  const [verdicts, setVerdicts] = useState({});
  const [feedbacks, setFeedbacks] = useState({});
  const [stage, setStage] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [log, setLog] = useState([]);
  const [regenCount, setRegenCount] = useState(0);
  const [userCredits, setUserCredits] = useState(9999); // TODO: Replace with real user credit fetch
  const [regenFee, setRegenFee] = useState(0); // Fee for next regeneration (in INR or USD)
  const [currency, setCurrency] = useState('INR'); // TODO: Replace with real user currency fetch
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisVerdict, setAnalysisVerdict] = useState(null); // "approved" | "rejected" | null
  const [analysisFeedback, setAnalysisFeedback] = useState("");
  const [approvedLearnings, setApprovedLearnings] = useState([]);
  const resRef = useRef(null);

  const setV = useCallback((i, v) => { setVerdicts(p => ({ ...p, [i]: v })); setSubmitted(false); }, []);
  const setFb = useCallback((i, t) => { setFeedbacks(p => ({ ...p, [i]: t })); }, []);

  // Helper: calculate regeneration fee (mocked, should be fetched from backend)
  const calcRegenFee = () => {
    // Example: INR, 10/15/20/25 for 15/30/60/60+ min, USD $0.30
    // Replace with backend call as needed
    if (currency === 'USD') return 0.3;
    return 10; // Default to 10 INR for demo
  };

  const analyze = useCallback(async (isRegen = false) => {
    if (!transcript.trim()) return;
    setError(null); setHooks(null); setVerdicts({}); setFeedbacks({}); setSubmitted(false);
    setAnalysis(null); setAnalysisVerdict(null); setAnalysisFeedback("");
    if (isRegen) {
      setRegenCount(c => c + 1);
      setRegenFee(calcRegenFee());
    } else {
      setRegenCount(0);
      setRegenFee(0);
    }
    setLoading(true);
    try {
      setStage("Streaming hook analysis…");
      const resp = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 4000,
          stream: true,
          messages: [{ role: "user", content: buildPrompt(niche, transcript, language) }],
        }),
      });
      if (!resp.ok) {
        const b = await resp.text();
        throw new Error(`API ${resp.status}: ${b.slice(0, 300)}`);
      }

      // ...existing code...
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";
      let hookCount = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
          try {
            const evt = JSON.parse(line.slice(6));
            if (evt.type === "content_block_delta" && evt.delta?.text) {
              accumulated += evt.delta.text;
              // Count hooks found so far for progress
              const newCount = (accumulated.match(/"rank"\s*:/g) || []).length;
              if (newCount > hookCount) {
                hookCount = newCount;
                setStage(`Found ${hookCount}/5 hooks…`);
                // Try to parse partial results for progressive rendering
                try {
                  const partial = accumulated.replace(/^```(?:json)?\s*/, "").replace(/,?\s*\]\s*\}?\s*$/, "]}");
                  const parsed = JSON.parse(partial);
                  if (parsed.hooks?.length > 0) setHooks([...parsed.hooks]);
                } catch { /* partial JSON not yet parseable */ }
              }
            }
          } catch { /* skip unparseable SSE lines */ }
        }
      }

      // Final parse
      const cleaned = accumulated.replace(/^```(?:json)?\s*/, "").replace(/\s*```$/, "").trim();
      const parsed = JSON.parse(cleaned);
      const arr = parsed.hooks || [];
      if (arr.length < 5) throw new Error(`Expected 5 hooks, got ${arr.length}. Try a longer transcript.`);
      setHooks(arr.slice(0, 5));
      setStage("");
      setTimeout(() => resRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch (e) {
      setError(e.message); setStage("");
    } finally { setLoading(false); }
  }, [transcript, niche, language, currency]);
  // Regeneration UI logic
  const isFirstRegenFree = regenCount === 0;
  const canRegenerate = isFirstRegenFree || userCredits >= regenFee;

  const hasVerdicts = Object.values(verdicts).some(v => v != null);
  const appCt = Object.values(verdicts).filter(v => v === "approve").length;
  const rejCt = Object.values(verdicts).filter(v => v === "reject").length;

  const submitAll = useCallback(() => {
    if (!hasVerdicts) return;
    setLog(prev => [{
      ts: new Date().toISOString(), niche, language,
      hooks: hooks.map((h, i) => ({
        rank: i + 1, type: h.hook_type, funnel_role: h.funnel_role,
        score: h.attention_score, text: h.hook_text?.slice(0, 140),
        verdict: verdicts[i] || "no_verdict", feedback: feedbacks[i] || "",
      })),
    }, ...prev]);
    setSubmitted(true);
  }, [hasVerdicts, hooks, verdicts, feedbacks, niche]);

  // ── FEEDBACK ANALYSIS ENGINE ──
  const generateAnalysis = useCallback(async () => {
    if (!submitted || !hooks) return;
    setAnalysisLoading(true); setAnalysis(null); setAnalysisVerdict(null); setAnalysisFeedback("");
    try {
      const sessionData = hooks.map((h, i) => ({
        rank: i + 1,
        hook_type: h.hook_type,
        funnel_role: h.funnel_role,
        attention_score: h.attention_score,
        scores: h.scores,
        hook_text: h.hook_text?.slice(0, 200),
        verdict: verdicts[i] || "no_verdict",
        feedback: feedbacks[i] || "",
      }));

      const existingLearnings = approvedLearnings.length > 0
        ? `\n\nPREVIOUSLY APPROVED LEARNINGS (${approvedLearnings.length} total):\n${approvedLearnings.map((l, i) => `${i + 1}. [${l.ts}] ${l.summary}`).join("\n")}`
        : "";

      const prompt = `You are an editorial intelligence analyst for HookCut, an AI-powered hook extraction tool for YouTube Shorts.

You are reviewing a feedback session where a human editor approved or rejected LLM-identified hooks. Your job is to extract actionable patterns that can improve the hook identification engine.

SESSION CONTEXT:
- Niche: ${niche}
- Language: ${language}
- Total hooks: 5
- Approved: ${Object.values(verdicts).filter(v => v === "approve").length}
- Rejected: ${Object.values(verdicts).filter(v => v === "reject").length}
- No verdict: ${Object.values(verdicts).filter(v => v == null).length}
${existingLearnings}

SESSION DATA:
${JSON.stringify(sessionData, null, 2)}

Analyze this feedback session and return a JSON object with:

{
  "session_summary": "One paragraph summarizing what happened in this session — what content was analyzed, what the editor liked vs rejected, any clear editorial preferences.",
  
  "approved_patterns": [
    {
      "pattern": "Name of the pattern observed in approved hooks",
      "description": "Specific description of WHY these hooks were approved. Be concrete.",
      "evidence": "Quote specific hook text or feedback that supports this"
    }
  ],
  
  "rejection_patterns": [
    {
      "pattern": "Name of the pattern observed in rejected hooks", 
      "description": "Specific description of WHY these hooks were rejected. Be concrete.",
      "evidence": "Quote specific feedback or hook text"
    }
  ],
  
  "proposed_rule_updates": [
    {
      "action": "add | modify | reinforce",
      "rule_id": "New rule letter or existing rule (A-Q) to modify",
      "current": "Current rule text if modifying, or 'N/A' if new",
      "proposed": "Proposed new or updated rule text",
      "rationale": "Why this change would improve hook identification"
    }
  ],
  
  "scoring_observations": [
    {
      "dimension": "Which scoring dimension (scroll_stop, curiosity_gap, etc.)",
      "observation": "Was the LLM over-scoring or under-scoring on this dimension? How should calibration change?"
    }
  ],
  
  "confidence": "low | medium | high — how confident are you in these patterns based on this single session? Low if only 1-2 verdicts, high if clear consistent patterns across all 5 hooks."
}

RULES FOR YOUR ANALYSIS:
- Be SPECIFIC. "Hooks were too long" is useless. "Hooks that exceeded 25 seconds were rejected because they included explanation after the curiosity peak" is useful.
- Reference the actual hook text and feedback when identifying patterns.
- If the editor's feedback explicitly states what was wrong, weight that heavily.
- If hooks with no verdict exist, note them but don't draw strong conclusions from them.
- Propose rule updates ONLY if you see a clear pattern — don't propose changes based on one data point.
- If this session doesn't reveal any new patterns (e.g., all hooks approved with no feedback), say so honestly.

Return ONLY valid JSON. No markdown fences.`;

      const resp = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 3000,
          messages: [{ role: "user", content: prompt }],
        }),
      });
      if (!resp.ok) throw new Error(`API ${resp.status}`);
      const data = await resp.json();
      const raw = data.content?.[0]?.text || "";
      const cleaned = raw.replace(/^```(?:json)?\s*/, "").replace(/\s*```$/, "").trim();
      setAnalysis(JSON.parse(cleaned));
    } catch (e) {
      setAnalysis({ error: e.message });
    } finally { setAnalysisLoading(false); }
  }, [submitted, hooks, verdicts, feedbacks, niche, language, approvedLearnings]);

  const approveAnalysis = useCallback(() => {
    if (!analysis || analysis.error) return;
    setAnalysisVerdict("approved");
    setApprovedLearnings(prev => [...prev, {
      ts: new Date().toISOString(),
      niche, language,
      summary: analysis.session_summary?.slice(0, 200) || "No summary",
      approved_patterns: analysis.approved_patterns || [],
      rejection_patterns: analysis.rejection_patterns || [],
      proposed_rule_updates: analysis.proposed_rule_updates || [],
      scoring_observations: analysis.scoring_observations || [],
      reviewer_feedback: analysisFeedback || "",
      confidence: analysis.confidence || "unknown",
    }]);
  }, [analysis, niche, language, analysisFeedback]);

  const rejectAnalysis = useCallback(() => {
    setAnalysisVerdict("rejected");
  }, []);

  const ni = NICHES[niche];

  return (
    <div style={{ "--mono": "'JetBrains Mono',monospace", minHeight: "100vh", background: "#07070c", color: "#e0e0f0", fontFamily: "'DM Sans','Segoe UI',system-ui,sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />

      {/* ── HEADER ── */}
      <div style={{ borderBottom: "1px solid #1a1a28", padding: "8px 16px", display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 16, fontWeight: 700 }}><span style={{ color: "#ff6b35" }}>🎣</span> HookCut</span>
        <span style={{ fontSize: 8, color: "#4a4a60", background: "#12121c", padding: "2px 6px", borderRadius: 8, fontWeight: 600, fontFamily: "var(--mono)" }}>v4 · PRD v3 · V0 dev</span>
        <span style={{ fontSize: 8, color: "#ff6b3580", fontFamily: "var(--mono)" }}>NyxPath AI Labs</span>
        <div style={{ flex: 1 }} />
        {log.length > 0 && <span style={{ fontSize: 9, color: "#ff6b35", fontFamily: "var(--mono)" }}>📚 {log.length} sessions</span>}
        {approvedLearnings.length > 0 && <span style={{ fontSize: 9, color: "#3b82f6", fontFamily: "var(--mono)" }}>🧠 {approvedLearnings.length} learnings</span>}
      </div>

      <div style={{ display: "flex", maxWidth: 1400, margin: "0 auto", minHeight: "calc(100vh - 38px)" }}>

        {/* ── LEFT PANEL ── */}
        <div style={{ width: 310, flexShrink: 0, padding: "12px 10px", borderRight: "1px solid #1a1a28", display: "flex", flexDirection: "column", gap: 8, overflowY: "auto" }}>

          {/* Niche + Language selectors */}
          <div style={{ display: "flex", gap: 6 }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 8, fontWeight: 700, color: "#4a4a60", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 3, display: "block" }}>Niche</label>
              <select value={niche} onChange={e => { setNiche(e.target.value); setHooks(null); setError(null); }} style={{
                width: "100%", padding: "7px 8px", background: "#12121c", color: "#e0e0f0",
                border: "1px solid #1c1c2c", borderRadius: 5, fontSize: 11, fontFamily: "inherit", outline: "none",
              }}>
                {Object.keys(NICHES).map(n => <option key={n}>{n}</option>)}
              </select>
            </div>
            <div style={{ width: 130, flexShrink: 0 }}>
              <label style={{ fontSize: 8, fontWeight: 700, color: "#4a4a60", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 3, display: "block" }}>Language</label>
              <select value={language} onChange={e => { setLanguage(e.target.value); setHooks(null); setError(null); }} style={{
                width: "100%", padding: "7px 8px", background: "#12121c", color: "#e0e0f0",
                border: "1px solid #1c1c2c", borderRadius: 5, fontSize: 11, fontFamily: "inherit", outline: "none",
              }}>
                {Object.entries(LANGUAGES).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
            </div>
          </div>

          {/* Niche info */}
          <div style={{ padding: "5px 8px", background: "#ff6b3508", borderRadius: 5, border: "1px solid #ff6b3512", fontSize: 9, color: "#ff6b35cc", lineHeight: 1.5, fontFamily: "var(--mono)" }}>
            {ni.softRange} · {language} · {ni.preferredTypes.slice(0, 3).join(" · ")}
          </div>

          {/* Transcript input */}
          <textarea value={transcript} onChange={e => { setTranscript(e.target.value); setHooks(null); setError(null); setSubmitted(false); }}
            placeholder={"[0:00] Paste full transcript here…\nTimestamps recommended but optional.\n\nThe full transcript goes to the LLM — no pre-filtering."}
            style={{
              flex: 1, minHeight: 180, padding: 9, background: "#0a0a12", color: "#e0e0f0",
              border: "1px solid #1a1a28", borderRadius: 6, fontSize: 10.5, lineHeight: 1.7,
              fontFamily: "var(--mono)", resize: "none", outline: "none",
            }}
          />

          {/* Sample + info */}
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <button onClick={() => { setTranscript(SAMPLE_TRANSCRIPT); setHooks(null); setError(null); setVerdicts({}); setFeedbacks({}); setSubmitted(false); }} style={{
              padding: "5px 10px", background: "#12121c", color: "#4a4a60", border: "1px solid #1c1c2c",
              borderRadius: 4, fontSize: 9, cursor: "pointer", fontFamily: "inherit",
            }}>Load sample</button>
            <span style={{ fontSize: 9, color: "#333", lineHeight: 1.3 }}>Pure LLM · 17 rules · EN/HI/Hinglish</span>
          </div>

          {/* Analyze / Regenerate */}
          <button onClick={() => analyze(false)} disabled={loading || !transcript.trim()} style={{
            padding: "10px", background: loading ? "#12121c" : "#ff6b35",
            color: loading ? "#4a4a60" : "#fff", border: "none", borderRadius: 6,
            fontSize: 12, fontWeight: 600, cursor: loading ? "wait" : "pointer",
            fontFamily: "inherit", opacity: !transcript.trim() ? 0.3 : 1,
          }}>
            {loading ? `⏳ ${stage}` : "🔍 Evaluate Hooks"}
          </button>

          {/* Regenerate (PRD v3 Section 08) */}
          {hooks && !loading && (
            <button onClick={() => analyze(true)} style={{
              padding: "7px", background: "#12121c", color: "#ff6b35aa",
              border: "1px solid #ff6b3520", borderRadius: 5, fontSize: 10, fontWeight: 500,
              cursor: "pointer", fontFamily: "inherit",
            }}>
              🔄 Regenerate{regenCount > 0 ? ` (${regenCount + 1})` : ""}{regenCount >= 1 ? " · ₹10-25" : " · Free"}
            </button>
          )}

          {/* Submit feedback */}
          {hooks && (
            <div style={{ padding: "8px", background: "#0d0d16", borderRadius: 6, border: "1px solid #1a1a28" }}>
              <div style={{ fontSize: 9, color: "#4a4a60", marginBottom: 4 }}>
                {appCt > 0 && <span style={{ color: "#22c55e" }}>✓ {appCt}</span>}
                {appCt > 0 && rejCt > 0 && <span style={{ color: "#333" }}> · </span>}
                {rejCt > 0 && <span style={{ color: "#ef4444" }}>✗ {rejCt}</span>}
                {!hasVerdicts && "Approve/reject hooks →"}
              </div>
              <button onClick={submitAll} disabled={!hasVerdicts || submitted} style={{
                width: "100%", padding: "8px", borderRadius: 5, fontSize: 11, fontWeight: 600,
                fontFamily: "inherit", cursor: hasVerdicts && !submitted ? "pointer" : "default",
                background: submitted ? "#22c55e10" : hasVerdicts ? "#ff6b35" : "#12121c",
                color: submitted ? "#22c55e" : hasVerdicts ? "#fff" : "#4a4a60",
                border: submitted ? "1px solid #22c55e30" : "none",
                opacity: !hasVerdicts ? 0.3 : 1,
              }}>
                {submitted ? "✓ Submitted" : "Submit All Feedback"}
              </button>
            </div>
          )}

          {submitted && (
            <div style={{ padding: "6px 8px", background: "#22c55e06", borderRadius: 4, border: "1px solid #22c55e15", fontSize: 9, color: "#6ee7b7", lineHeight: 1.4 }}>
              ✅ Feedback logged.
            </div>
          )}

          {/* Generate Analysis button — appears after feedback submitted */}
          {submitted && !analysisLoading && !analysis && (
            <button onClick={generateAnalysis} style={{
              padding: "8px", background: "#3b82f615", color: "#3b82f6",
              border: "1px solid #3b82f625", borderRadius: 5, fontSize: 10, fontWeight: 600,
              cursor: "pointer", fontFamily: "inherit",
            }}>
              🧠 Analyze Feedback → Extract Learnings
            </button>
          )}
          {analysisLoading && (
            <div style={{ padding: "6px 8px", background: "#3b82f608", borderRadius: 4, border: "1px solid #3b82f615", fontSize: 9, color: "#3b82f6" }}>
              ⏳ Analyzing feedback patterns…
            </div>
          )}

          {/* Learning log */}
          {log.length > 0 && (
            <details style={{ fontSize: 9 }}>
              <summary style={{ color: "#4a4a60", cursor: "pointer", fontFamily: "var(--mono)" }}>📚 Session Log ({log.length})</summary>
              <pre style={{
                marginTop: 3, padding: 6, background: "#07070c", borderRadius: 4,
                fontSize: 8, fontFamily: "var(--mono)", color: "#3a3a50",
                overflowX: "auto", maxHeight: 140, lineHeight: 1.3, whiteSpace: "pre-wrap", border: "1px solid #1a1a28",
              }}>{JSON.stringify(log, null, 2)}</pre>
            </details>
          )}

          {/* Approved learnings */}
          {approvedLearnings.length > 0 && (
            <details style={{ fontSize: 9 }}>
              <summary style={{ color: "#3b82f6", cursor: "pointer", fontFamily: "var(--mono)" }}>🧠 Approved Learnings ({approvedLearnings.length})</summary>
              <div style={{ marginTop: 3, display: "flex", flexDirection: "column", gap: 3 }}>
                {approvedLearnings.map((l, i) => (
                  <div key={i} style={{ padding: "4px 6px", background: "#3b82f606", borderRadius: 3, border: "1px solid #3b82f610", fontSize: 8, color: "#6b8fc7", lineHeight: 1.4 }}>
                    <div style={{ fontWeight: 600, color: "#3b82f6" }}>#{i + 1} · {l.niche} · {l.confidence}</div>
                    <div>{l.summary}</div>
                    {l.proposed_rule_updates?.length > 0 && (
                      <div style={{ color: "#f59e0b", marginTop: 2 }}>
                        {l.proposed_rule_updates.map(r => `${r.action.toUpperCase()} ${r.rule_id}`).join(" · ")}
                      </div>
                    )}
                    {l.reviewer_feedback && <div style={{ color: "#5a5a72", fontStyle: "italic", marginTop: 1 }}>Note: {l.reviewer_feedback}</div>}
                  </div>
                ))}
              </div>
              <button onClick={() => {
                const blob = new Blob([JSON.stringify(approvedLearnings, null, 2)], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a"); a.href = url; a.download = `hookcut_learnings_${Date.now()}.json`; a.click(); URL.revokeObjectURL(url);
              }} style={{
                marginTop: 4, padding: "4px 8px", background: "#12121c", color: "#3b82f6",
                border: "1px solid #3b82f620", borderRadius: 3, fontSize: 8, cursor: "pointer", fontFamily: "inherit",
              }}>
                ⬇ Export Learnings JSON
              </button>
            </details>
          )}

          {/* Disclaimer (PRD v3 Section 15) */}
          <div style={{ fontSize: 8, color: "#2a2a3a", lineHeight: 1.4, marginTop: "auto", paddingTop: 8 }}>
            Scores are LLM estimates, not guarantees of performance. Ensure you have rights to the source content before generating Shorts.
          </div>
        </div>

        {/* ── RIGHT PANEL ── */}
        <div ref={resRef} style={{ flex: 1, padding: "12px 14px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
          {!hooks && !error && !loading && (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 6, opacity: 0.2 }}>
              <div style={{ fontSize: 34 }}>🎣</div>
              <div style={{ fontSize: 11, color: "#4a4a60", textAlign: "center", maxWidth: 220, lineHeight: 1.6 }}>
                Paste transcript → pick niche → <strong style={{ color: "#ff6b35" }}>Evaluate</strong>
              </div>
            </div>
          )}
          {error && (
            <div style={{ padding: 10, background: "#ef44440a", border: "1px solid #ef444420", borderRadius: 7, color: "#fca5a5", fontSize: 11, lineHeight: 1.6 }}>
              <strong>Error:</strong> {error}
            </div>
          )}
          {hooks?.map((h, i) => (
            <HookCard key={i} hook={h} index={i} verdict={verdicts[i]} onVerdict={setV} fb={feedbacks[i]} onFb={setFb} />
          ))}

          {/* ── ANALYSIS REVIEW PANEL ── */}
          {analysis && !analysis.error && (
            <div style={{ background: "#0a0a14", border: "1px solid #3b82f620", borderRadius: 10, overflow: "hidden", marginTop: 4 }}>
              <div style={{ padding: "10px 14px", borderBottom: "1px solid #3b82f612", display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 14 }}>🧠</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: "#3b82f6" }}>Feedback Analysis</span>
                <span style={{
                  fontSize: 9, padding: "2px 6px", borderRadius: 6, fontWeight: 600, fontFamily: "var(--mono)",
                  background: analysis.confidence === "high" ? "#22c55e15" : analysis.confidence === "medium" ? "#f59e0b15" : "#ef444415",
                  color: analysis.confidence === "high" ? "#22c55e" : analysis.confidence === "medium" ? "#f59e0b" : "#ef4444",
                }}>
                  {analysis.confidence} confidence
                </span>
                {analysisVerdict === "approved" && <span style={{ fontSize: 9, color: "#22c55e", fontWeight: 700 }}>✓ APPROVED</span>}
                {analysisVerdict === "rejected" && <span style={{ fontSize: 9, color: "#ef4444", fontWeight: 700 }}>✗ DISCARDED</span>}
              </div>

              <div style={{ padding: "12px 14px", display: "flex", flexDirection: "column", gap: 12 }}>
                {/* Summary */}
                <div style={{ fontSize: 12, color: "#b8b8cc", lineHeight: 1.7 }}>{analysis.session_summary}</div>

                {/* Approved patterns */}
                {analysis.approved_patterns?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "#22c55e", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 6 }}>✓ Patterns in Approved Hooks</div>
                    {analysis.approved_patterns.map((p, i) => (
                      <div key={i} style={{ marginBottom: 8, padding: "8px 10px", background: "#22c55e06", borderRadius: 6, border: "1px solid #22c55e10" }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: "#22c55e", marginBottom: 3 }}>{p.pattern}</div>
                        <div style={{ fontSize: 11, color: "#9a9ab0", lineHeight: 1.6 }}>{p.description}</div>
                        {p.evidence && <div style={{ fontSize: 10, color: "#5a5a72", marginTop: 3, fontStyle: "italic" }}>Evidence: {p.evidence}</div>}
                      </div>
                    ))}
                  </div>
                )}

                {/* Rejection patterns */}
                {analysis.rejection_patterns?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "#ef4444", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 6 }}>✗ Patterns in Rejected Hooks</div>
                    {analysis.rejection_patterns.map((p, i) => (
                      <div key={i} style={{ marginBottom: 8, padding: "8px 10px", background: "#ef444406", borderRadius: 6, border: "1px solid #ef444410" }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: "#ef4444", marginBottom: 3 }}>{p.pattern}</div>
                        <div style={{ fontSize: 11, color: "#9a9ab0", lineHeight: 1.6 }}>{p.description}</div>
                        {p.evidence && <div style={{ fontSize: 10, color: "#5a5a72", marginTop: 3, fontStyle: "italic" }}>Evidence: {p.evidence}</div>}
                      </div>
                    ))}
                  </div>
                )}

                {/* Proposed rule updates */}
                {analysis.proposed_rule_updates?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "#f59e0b", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 6 }}>⚡ Proposed Rule Updates</div>
                    {analysis.proposed_rule_updates.map((r, i) => (
                      <div key={i} style={{ marginBottom: 8, padding: "8px 10px", background: "#f59e0b06", borderRadius: 6, border: "1px solid #f59e0b10" }}>
                        <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 3 }}>
                          <span style={{ fontSize: 9, padding: "1px 5px", borderRadius: 4, background: r.action === "add" ? "#22c55e15" : r.action === "modify" ? "#f59e0b15" : "#3b82f615", color: r.action === "add" ? "#22c55e" : r.action === "modify" ? "#f59e0b" : "#3b82f6", fontWeight: 700, textTransform: "uppercase" }}>{r.action}</span>
                          <span style={{ fontSize: 11, fontWeight: 600, color: "#f59e0b" }}>Rule {r.rule_id}</span>
                        </div>
                        {r.current && r.current !== "N/A" && <div style={{ fontSize: 10, color: "#5a5a72", marginBottom: 2 }}>Current: {r.current}</div>}
                        <div style={{ fontSize: 11, color: "#b8b8cc", lineHeight: 1.6 }}>Proposed: {r.proposed}</div>
                        <div style={{ fontSize: 10, color: "#5a5a72", marginTop: 2 }}>Rationale: {r.rationale}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Scoring observations */}
                {analysis.scoring_observations?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "#a855f7", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 6 }}>📊 Scoring Calibration</div>
                    {analysis.scoring_observations.map((s, i) => (
                      <div key={i} style={{ marginBottom: 4, fontSize: 11, color: "#9a9ab0", lineHeight: 1.6 }}>
                        <span style={{ fontWeight: 600, color: "#a855f7" }}>{s.dimension}: </span>{s.observation}
                      </div>
                    ))}
                  </div>
                )}

                {/* Reviewer feedback + approve/reject */}
                {!analysisVerdict && (
                  <div style={{ borderTop: "1px solid #1a1a28", paddingTop: 10, display: "flex", flexDirection: "column", gap: 6 }}>
                    <textarea
                      value={analysisFeedback} onChange={e => setAnalysisFeedback(e.target.value)}
                      placeholder="Your feedback on this analysis (optional — add corrections, disagreements, or additional context)…"
                      style={{
                        width: "100%", padding: "8px 10px", background: "#07070c", color: "#e0e0f0",
                        border: "1px solid #1c1c2c", borderRadius: 5, fontSize: 11, fontFamily: "inherit",
                        outline: "none", resize: "vertical", minHeight: 50, lineHeight: 1.5, boxSizing: "border-box",
                      }}
                    />
                    <div style={{ display: "flex", gap: 6 }}>
                      <button onClick={approveAnalysis} style={{
                        flex: 1, padding: "9px", borderRadius: 6, fontSize: 11, fontWeight: 600,
                        fontFamily: "inherit", cursor: "pointer",
                        background: "#22c55e", color: "#fff", border: "none",
                      }}>✓ Approve — Add to Learnings</button>
                      <button onClick={rejectAnalysis} style={{
                        flex: 1, padding: "9px", borderRadius: 6, fontSize: 11, fontWeight: 600,
                        fontFamily: "inherit", cursor: "pointer",
                        background: "#0a0a12", color: "#ef4444", border: "1.5px solid #ef444430",
                      }}>✗ Discard</button>
                    </div>
                  </div>
                )}

                {analysisVerdict === "approved" && (
                  <div style={{ padding: "6px 8px", background: "#22c55e08", borderRadius: 4, border: "1px solid #22c55e15", fontSize: 10, color: "#6ee7b7", lineHeight: 1.4 }}>
                    ✅ Analysis approved and added to learnings log ({approvedLearnings.length} total).
                    {analysisFeedback && <div style={{ marginTop: 3, color: "#5a5a72" }}>Your note: "{analysisFeedback}"</div>}
                  </div>
                )}
                {analysisVerdict === "rejected" && (
                  <div style={{ padding: "6px 8px", background: "#ef444408", borderRadius: 4, border: "1px solid #ef444415", fontSize: 10, color: "#fca5a5" }}>
                    Discarded. No changes saved.
                  </div>
                )}
              </div>
            </div>
          )}

          {analysis?.error && (
            <div style={{ padding: 10, background: "#ef44440a", border: "1px solid #ef444420", borderRadius: 7, color: "#fca5a5", fontSize: 11 }}>
              Analysis error: {analysis.error}
            </div>
          )}
        </div>
      </div>

      <style>{`
        select:focus,textarea:focus,input:focus{border-color:#ff6b35 !important}
        button:hover:not(:disabled){filter:brightness(1.1)}
        ::-webkit-scrollbar{width:4px}
        ::-webkit-scrollbar-track{background:#07070c}
        ::-webkit-scrollbar-thumb{background:#1c1c2c;border-radius:2px}
        details>summary{list-style:none}
        details>summary::-webkit-details-marker{display:none}
      `}</style>
    </div>
  );
}
