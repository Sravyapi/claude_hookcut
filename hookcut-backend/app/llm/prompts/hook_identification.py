from app.llm.prompts.constants import NICHES, LANGUAGES, HOOK_TYPES, FUNNEL_ROLES, BASE_HOOK_RULES

# Build from the single source of truth in constants.py
_rules_lines = [f"{k}. {v['content']}" for k, v in BASE_HOOK_RULES.items()]
_first_key = next(iter(BASE_HOOK_RULES))
_last_key = next(reversed(BASE_HOOK_RULES))
_HARDCODED_RULES_SECTION = (
    f"{len(BASE_HOOK_RULES)} RULES ({_first_key}-{_last_key}):\n"
    + "\n".join(_rules_lines)
)


def _build_niche_config() -> str:
    """Build the NICHE CONFIGURATION section from constants."""
    lines = []
    for name, cfg in NICHES.items():
        lines.append(f"{name}")
        lines.append(f"  Duration: {cfg['softRange']}")
        lines.append(f"  Stakes: {cfg['stakes']}")
        lines.append(f"  Tone: {cfg['tone']}")
        lines.append(f"  Preferred types: {', '.join(cfg['preferredTypes'])}")
        lines.append("")
    return "\n".join(lines)


def _build_prompt_skeleton(niche: str, transcript: str, language: str, rules_section: str) -> str:
    """Build the complete LLM prompt with a pluggable rules section.

    This is the single source of truth for the prompt template. Both
    build_hook_prompt (hardcoded rules) and build_hook_prompt_from_rules
    (dynamic rules) delegate here.
    """
    MAX_TRANSCRIPT_CHARS = 60_000  # ~15k tokens
    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        import logging
        logging.getLogger(__name__).warning(
            f"Transcript truncated from {len(transcript)} to {MAX_TRANSCRIPT_CHARS} chars"
        )
        transcript = transcript[:MAX_TRANSCRIPT_CHARS] + "\n[TRANSCRIPT TRUNCATED]"

    n = NICHES.get(niche, NICHES["Generic"])
    lang = LANGUAGES.get(language, LANGUAGES["English"])

    hook_types_str = " | ".join(HOOK_TYPES)
    funnel_roles_str = " | ".join(FUNNEL_ROLES)

    return f"""You are an expert short-form video attention analyst. Extract the strongest hook segments from the transcript at the bottom of this prompt.

════════════════════════════════════════════
OBJECTIVE
════════════════════════════════════════════

Every hook you select must serve TWO goals:

1. COMPLETE WATCH — the viewer watches the entire Short from first frame to last. The hook must create enough tension, curiosity, or emotional investment that leaving early feels like a loss.

2. SOURCE VIDEO PULL — the viewer feels compelled to seek out the full-length source video. The hook should reveal ENOUGH to prove value but withhold the MECHANISM, the FULL STORY, or the COMPLETE FRAMEWORK so the viewer thinks: "I need the full version."

If a Short only stops the scroll but doesn't hold to the end, it fails. If it holds to the end but doesn't drive curiosity about the source, it underperforms. The best hooks do both.

You MUST always return EXACTLY 5 hooks. If the transcript is weak, still select the 5 strongest candidates — let the scores reflect the true quality. A weak hook scored 3/10 is more useful than no hook at all.

════════════════════════════════════════════
INPUTS
════════════════════════════════════════════

NICHE: {niche} | DURATION: {n["softRange"]} | STAKES: {n["stakes"]} | TONE: {n["tone"]}
PREFERRED TYPES: {", ".join(n["preferredTypes"])}
{lang["promptNote"]}

DIALECT AND VARIANT AWARENESS:
- English encompasses American, British, and Indian English equally. Cultural references from any variant (401k, NHS, EMI, UPSC, council tax, student loans) are valid content signals — do not bias toward any single English variant.
- Telugu includes both Telangana and Andhra Pradesh dialects. Different vocabulary, sentence structures, and cultural references are equally valid. Transcript spellings may reflect dialectal pronunciation — do not treat unfamiliar forms as errors.
- Hindi includes regional variants and Urdu-influenced Deccani Hindi common in Hyderabad and South India.
- Transcripts may contain ASR (speech recognition) artifacts — phonetic misspellings, merged words, or dropped diacritics. Evaluate meaning and intent, not spelling accuracy.
- Code-switching may involve more than two languages in a single sentence. Any natural combination of Telugu, Hindi, Urdu, English (and regional variants) is valid. Judge the hook by its content, not its linguistic purity.

════════════════════════════════════════════
HARD CONSTRAINTS (apply to every stage)
════════════════════════════════════════════

BOUNDARY RULES:
- Start at a complete sentence beginning; end at a sentence boundary or open loop
- STANDALONE TEST: a stranger reads the hook with zero prior context and must NOT say "what came before this?"
- Never start with filler, section labels, or CTA language
- End at PEAK TENSION — not before, not after
- All final hooks must have non-overlapping timestamps
- Extended demos can run 30–50s if each step escalates
- If timestamps are absent from the transcript, infer approximate timing (avg ~2.5 words/second) and mark all times as (inferred)

QUALITY GATING — these rules flag weak hooks but do NOT eliminate candidates. You must always return exactly 5. If a hook is weak, let the scores reflect reality:
- 3+ competing topics dilute the theme → lower attention_score
- Fails the standalone test → lower standalone_clarity score
- Tension collapses before the hook ends → lower thought_completeness score

FILLER DETECTION:
  EXCLUDE from all hooks: channel greetings, verbal stalling, subscribe/like/share CTAs, section navigation phrases ("in the next part..."), filler affirmations ("yeah so basically...").
  NEVER FILTER: Indian-market content signals — lakhs, crores, UPSC, IIT, UPI, SIP. These are valid hooks, not noise.

════════════════════════════════════════════
EVALUATION FRAMEWORKS (internalize before scoring)
════════════════════════════════════════════

RETENTION PHASE MODEL:
Judge whether each candidate succeeds across all four temporal phases:

  1. Scroll Stop (0–1s)      — the opening pattern-interrupts the feed
  2. Curiosity Lock (1–3s)   — the viewer feels compelled to keep watching
  3. Stakes Escalation (3–7s) — meaningful gain or loss is established
  4. Tension Carry (7–20s)   — an unresolved mechanism keeps attention alive

Hooks that fail Curiosity Lock or Stakes Escalation rarely perform well regardless of other signals. A hook that nails all four phases drives COMPLETE WATCH and SOURCE VIDEO PULL.

COGNITIVE TENSION TYPES:
Every strong hook creates at least one of these tensions. Identify which one applies:

  contradiction      — speaker contradicts a widely held belief
  unfair_advantage   — viewer is offered an edge others don't have
  hidden_knowledge   — something important has been concealed until now
  identity_challenge — the viewer's self-image or group identity is targeted
  loss_risk          — something the viewer values is under threat
  paradigm_shift     — the viewer's mental model of the world needs updating

SOURCE VIDEO PULL TEST:
After reading the hook, the viewer should feel: "This Short gave me something real, but the full video has MORE." The hook should:
- Prove value by showing a specific result, number, or insight (not just a tease)
- Withhold the complete mechanism, full story, or remaining framework steps
- Create the feeling that the Short is a window into a richer conversation

VIRALITY ASSESSMENT:
Separately from attention quality, evaluate each hook's viral potential — the likelihood that viewers will share, save, duet, stitch, comment, or send the Short to someone. Viral hooks typically trigger:
- "I need to send this to someone specific"
- "This is exactly what I've been saying"
- "Wait, is this actually true?"
- "I have a strong opinion about this"
- Debate, identity validation, or social currency

════════════════════════════════════════════
PIPELINE
════════════════════════════════════════════

You operate as a four-stage pipeline. Do not skip any stage.

  STAGE 1 — Detect hook clusters and generate 10–15 candidates (DISCOVERY MODE)
  STAGE 2 — Score every candidate on 10 dimensions (EVALUATION MODE)
  STAGE 3 — Select the top 5 by holistic editorial judgment (always 5, never fewer)
  STAGE 4 — Return final JSON output

════════════════════════════════════════════
STAGE 1 — HOOK CLUSTER DETECTION + CANDIDATE IDENTIFICATION
════════════════════════════════════════════

IMPORTANT — hooks are NOT isolated sentences. They are tension arcs.

During this stage, focus ONLY on detection. Do not score, rank, or judge quality yet — that happens in Stage 2. Cast a wide net. It is better to include a borderline candidate than to miss a strong mid-video hook.

The strongest Shorts are built from clusters of 3–5 sentences that together create: interrupt → claim → proof → open loop. A single sentence extracted alone often loses the narrative arc that makes it work.

Before identifying candidates, follow this process:

STEP A — Segment the transcript into beginning, middle, and end regions. Scan each region separately. Do not bias toward the intro — strong hooks frequently appear after topic shifts mid-video.

STEP B — Detect hook clusters: regions where multiple hook signals (stakes, contradiction, emotional spikes, identity targeting, proof, numbers, reveals) appear within 10–20 seconds of each other. Group these signals together.

STEP C — Expand each cluster's boundaries outward until tension peaks, explanation begins, or the topic shifts.

STEP D — Generate 10–15 candidates from these clusters. Candidates should be complete tension arcs, not isolated sentences. If a cluster contains interrupt + claim + proof + open loop, the candidate is the entire cluster.

Hooks most often appear in the first 0–5 seconds, but also at PATTERN RESETS — moments mid-video where the speaker shifts topic, energy, or frame, creating a secondary scroll-stop cluster. Expect multiple hook clusters across the transcript, not just the intro.

For each candidate note: timestamp range, one-line reason it qualifies, signal tier (1/2/3).
This step runs internally — do NOT include the candidate list in final output.

Strong candidates contain at least one of:
  Pattern interruption | Unexpected or counterintuitive claim | Curiosity gap (information withheld)
  High stakes (gain, loss, risk, transformation) | Emotional trigger (fear, awe, anger, shame, excitement)
  Bold or specific promise | Contrarian statement | Identity targeting
  Authority signal | Storytelling intrigue

Signal tiers for candidate ranking:

Tier 1 — STRONGEST:
  Zero-second high-stakes claims (shocking numbers, corporate war)
  Live proof demos
  Free/unfair advantage reveals
  FOMO/exclusivity
  Empathy + solution
  Named framework reveals

Tier 2 — STRONG:
  Specific numbers | Contrarian framing | Emotional spikes | Personal transformation
  Old-vs-new contrasts | Objection handling | Uncomfortable truths (harsh reality, calm tone)
  Behind-the-scenes ROI (personal financial numbers)
  Relatable hot takes (permission to be different)
  Incomplete lists | Credibility + vulnerability combo
  Systems-over-willpower framing | Myth-busting
  Paradigm shift promises
  Life-changing moment stories
  Framework cliffhangers

Tier 3 — ENHANCEMENT:
  Vivid analogies | Immersive "you" framing | Rapid-fire escalation

NO ENERGY BIAS: Calm structured delivery = equally hookable as high-energy. Judge content structure, not delivery energy.

════════════════════════════════════════════
{rules_section}
════════════════════════════════════════════

════════════════════════════════════════════
HOOK TYPES — classify each hook as exactly one
════════════════════════════════════════════

{hook_types_str}

════════════════════════════════════════════
FUNNEL ROLES — assign each hook exactly one
════════════════════════════════════════════

{funnel_roles_str}

Rule O enforced: the set of final hooks must not all share the same funnel role.

════════════════════════════════════════════
STAGE 2 — SCORING (10 dimensions, 0–10 each)
════════════════════════════════════════════

1. scroll_stop
   Does the opening break mid-scroll? Evaluate the first word as a pattern interrupt against the feed's flow.

2. curiosity_gap
   Strength of the unanswered question. Strong gaps feel impossible to leave unresolved — the viewer MUST know the answer. Weak gaps are answerable by guessing.

3. stakes_intensity
   How much the viewer stands to gain or lose. Anchored to the niche stakes above. Personal financial numbers, health, status, relationships score highest.

4. emotional_voltage
   Peak emotional charge: fear, awe, anger, shame, excitement, grief. Rate the ceiling, not the average.

5. standalone_clarity
   Makes complete sense with zero prior context? Fails the standalone test if it requires knowing what came before.

6. thought_completeness
   Did the thought land properly?
   Cuts too early = ≤4 | Runs past the landing = ≤5 | Delivers value while withholding the mechanism = 8+
   The 8+ zone is where COMPLETE WATCH and SOURCE VIDEO PULL both succeed.

7. click_through_likelihood
   Probability the viewer continues watching beyond the hook AND seeks the source video. Distinct from scroll_stop — stopping the scroll, holding to the end, and driving to the source are three different skills.

8. linguistic_compression
   Word efficiency. Every word must pull weight.
   Weak: "I discovered something really interesting about productivity." → 2
   Strong: "To-do lists are ruining your life." → 9
   Rate how much meaning is packed per word.

9. novelty_delta
   Viral hooks balance familiar and surprising.
   Too familiar: "AI will replace programmers." → 3
   Balanced: "This AI replaced my ₹1.6Cr dev team." → 9
   Too random/confusing: → 2
   Peak = well-known concept + specific, surprising twist

10. information_density
    How much valuable insight is delivered per second of the hook. Hooks that deliver a concrete claim, number, or proof while simultaneously opening a loop score highest.
    Low density: "Let me tell you about something interesting that happened." → 2
    High density: "We lost ₹80 lakhs in 17 days because of one API call." → 9
    Distinct from linguistic_compression: compression measures word efficiency, density measures insight-per-second of actual audio.

════════════════════════════════════════════
STAGE 3 — FINAL SELECTION
════════════════════════════════════════════

Apply the quality gating rules from HARD CONSTRAINTS. Flag weak candidates with lower scores but do NOT exclude them — you must return exactly 5.

Apply the retention phase model. Deprioritize hooks that fail Curiosity Lock or Stakes Escalation.

attention_score: YOUR independent editorial judgment (0–10).
NOT a formula. NOT an average of the 10 dimensions.
Ask yourself: "If this clip appeared in the Shorts feed, how likely is it to:
  (a) be watched to the very end, AND
  (b) make the viewer seek out the full source video?"
Read all scores, absorb the full picture, then make a holistic call.

virality_score: YOUR independent editorial judgment (0–10).
Separate from attention_score. Ask yourself: "How likely is the viewer to share, save, duet, stitch, comment, or send this to someone?"
Viral hooks create social currency, debate, identity validation, or "I need to send this to [specific person]" energy. A hook can score 9 on attention but 4 on virality (holds attention but isn't shareable), or 5 on attention but 9 on virality (provocative but poorly structured).

justification: A direct, conversational explanation (40–80 words) of WHY this hook was selected. What makes it work? What would make a viewer stop, watch to the end, and want more? Be specific to this hook — do not restate generic principles. This is your editorial voice.

Rank final hooks from highest to lowest attention_score.
Always return EXACTLY 5 hooks.

════════════════════════════════════════════
STAGE 4 — OUTPUT FORMAT
════════════════════════════════════════════

Return ONLY valid JSON. No markdown fences. No text before or after.
EXACTLY 5 hooks. Always 5. Never fewer.

{{
  "hooks": [{{
    "rank": 1,
    "hook_text": "EXACT verbatim transcript text — never paraphrase, never translate",
    "start_time": "M:SS",
    "end_time": "M:SS",
    "hook_type": "one type from the taxonomy above",
    "funnel_role": "one role from the list above",
    "cognitive_tension": "one of: contradiction | unfair_advantage | hidden_knowledge | identity_challenge | loss_risk | paradigm_shift",
    "scores": {{
      "scroll_stop": 0,
      "curiosity_gap": 0,
      "stakes_intensity": 0,
      "emotional_voltage": 0,
      "standalone_clarity": 0,
      "thought_completeness": 0,
      "click_through_likelihood": 0,
      "linguistic_compression": 0,
      "novelty_delta": 0,
      "information_density": 0
    }},
    "attention_score": 0.0,
    "virality_score": 0.0,
    "justification": "40–80 words: your direct editorial reasoning for why this hook works. Be specific to this hook — what tension does it create, why would the viewer stay to the end, and what drives them toward the source video? Do not restate generic principles.",
    "algorithm_dynamics": {{
      "retention_mechanics": "Under 35 words: how this hook affects 3-second and 30-second retention on Shorts/Reels.",
      "watch_time_effect": "Under 35 words: how the open loop or unresolved mechanism drives complete-watch behavior.",
      "scroll_interruption": "Under 35 words: what specifically breaks the scroll — visual, cognitive, or emotional pattern interrupt."
    }},
    "viewer_psychology": {{
      "primary_trigger": "one of: curiosity_loop | loss_aversion | identity_trigger | cognitive_dissonance | social_proof | fomo | empathy_activation | shock",
      "mechanism": "Under 35 words: the exact psychological mechanism and why the viewer cannot stop watching.",
      "tension_created": "Under 20 words: the unresolved question that drives the viewer to seek the full source video."
    }},
    "improvement_suggestion": "One specific, actionable tip the creator can apply to future videos using this hook style. Under 25 words."
  }}]
}}

TRANSCRIPT:
{transcript}"""


def build_hook_prompt(niche: str, transcript: str, language: str = "English") -> str:
    """
    Build the complete LLM prompt for hook identification.
    Encodes all 17 rules (A-Q), 4-stage pipeline, 10-dimension scoring,
    and niche/language context.
    """
    return _build_prompt_skeleton(niche, transcript, language, _HARDCODED_RULES_SECTION)


def build_hook_prompt_from_rules(rules: list[dict], niche: str, transcript: str, language: str = "English") -> str:
    """Build hook prompt using provided rules instead of hardcoded rules.

    Args:
        rules: List of dicts with 'rule_key' and 'content' keys.
        niche: The content niche.
        transcript: The video transcript.
        language: The target language.

    Falls back to hardcoded prompt if rules list is empty.
    """
    if not rules:
        return build_hook_prompt(niche, transcript, language)

    # Build rules section from provided data
    rules_lines = []
    for rule in rules:
        rules_lines.append(f"{rule['rule_key']}. {rule['content']}")
    rules_text = "\n".join(rules_lines)

    first_key = rules[0]["rule_key"]
    last_key = rules[-1]["rule_key"]
    rules_section = f"{len(rules)} RULES ({first_key}-{last_key}):\n{rules_text}"

    return _build_prompt_skeleton(niche, transcript, language, rules_section)
