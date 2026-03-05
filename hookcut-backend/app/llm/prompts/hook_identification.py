from app.llm.prompts.constants import NICHES, LANGUAGES, HOOK_TYPES, FUNNEL_ROLES

_HARDCODED_RULES_SECTION = """17 RULES (A-Q):
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
Q. Workflow demos: include full step-by-step sequence, don't cut mid-demo"""


def _build_prompt_skeleton(niche: str, transcript: str, language: str, rules_section: str) -> str:
    """Build the complete LLM prompt with a pluggable rules section.

    This is the single source of truth for the prompt template. Both
    build_hook_prompt (hardcoded rules) and build_hook_prompt_from_rules
    (dynamic rules) delegate here.
    """
    n = NICHES.get(niche, NICHES["Generic"])
    lang = LANGUAGES.get(language, LANGUAGES["English"])

    hook_types_str = "|".join(HOOK_TYPES)
    funnel_roles_str = "|".join(FUNNEL_ROLES)

    return f"""You are a hook evaluator for YouTube Shorts. Extract the 5 best hook segments from this transcript.

NICHE: {niche} | DURATION: {n["softRange"]} | STAKES: {n["stakes"]} | TONE: {n["tone"]}
PREFERRED TYPES: {", ".join(n["preferredTypes"])}
{lang["promptNote"]}

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

{rules_section}

SCORING (7 dimensions, 0-10, holistic):
scroll_stop | curiosity_gap | stakes_intensity | emotional_voltage | standalone_clarity | thematic_focus (GATING: <5 = not top 3) | thought_completeness (cuts early ≤4, past landing ≤5, delivers value while withholding = 8+)
attention_score: YOUR independent editorial judgment (0-10), NOT a formula.

CLASSIFY each hook:
TYPE: {hook_types_str}
FUNNEL ROLE: {funnel_roles_str}

OUTPUT: Return ONLY valid JSON, no markdown. EXACTLY 5 hooks. Keep explanations CONCISE (under 30 words each).
{{
  "hooks": [{{
    "rank": 1,
    "hook_text": "EXACT verbatim transcript text",
    "start_time": "M:SS",
    "end_time": "M:SS",
    "hook_type": "primary type",
    "funnel_role": "role",
    "scores": {{"scroll_stop":0,"curiosity_gap":0,"stakes_intensity":0,"emotional_voltage":0,"standalone_clarity":0,"thematic_focus":0,"thought_completeness":0}},
    "attention_score": 0.0,
    "platform_dynamics": "Under 30 words: pattern interrupt + open loop + algorithm boost",
    "viewer_psychology": "Under 30 words: curiosity gap + tension + grounding",
    "improvement_suggestion": "One specific, actionable tip for how the creator could use this hook style in future videos (under 25 words)"
  }}]
}}

TRANSCRIPT:
{transcript}"""


def build_hook_prompt(niche: str, transcript: str, language: str = "English") -> str:
    """
    Build the complete LLM prompt for hook identification.
    Encodes all 17 rules (A-Q), 3-tier signal patterns, scoring dimensions,
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
