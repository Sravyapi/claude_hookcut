# Ported from hookcut_engine.jsx — source of truth for all LLM prompt construction.
# LANGUAGES: 3 supported languages (Telugu, Hindi, English) with code-switching support
# NICHES: 8 entries from hookcut_v4_prd3.jsx NICHES config
# HOOK_TYPES: 18 entries — union of PRD (13) + engine (15)
# FUNNEL_ROLES: 6 entries
# SCORE_DIMENSIONS: 7 entries (engine's holistic approach)

LANGUAGES = {
    "English": {
        "label": "English",
        "promptNote": (
            "LANGUAGE: English — may include natural code-switching with Hindi or Telugu. "
            "Hinglish (Hindi+English) and Tenglish (Telugu+English) mixing within sentences is "
            "common and acceptable. Output hook_text in the ORIGINAL mixed language exactly as "
            "spoken — NEVER normalize or translate."
        ),
    },
    "Hindi": {
        "label": "Hindi",
        "promptNote": (
            "LANGUAGE: Hindi (Devanagari or romanized) — code-switching to English for technical "
            "terms and to Telugu for regional references is normal. This is Hinglish territory: "
            "both languages may flow within the same sentence. Output hook_text in the ORIGINAL "
            "mixed language exactly as spoken — NEVER translate or normalize to pure Hindi."
        ),
    },
    "Telugu": {
        "label": "Telugu",
        "promptNote": (
            "LANGUAGE: Telugu — code-switching to English for technical/business terms and to "
            "Hindi for cultural references is very common (Tenglish). All three languages may "
            "appear within the same sentence. Output hook_text in the ORIGINAL mixed language "
            "exactly as spoken — NEVER translate or normalize to pure Telugu."
        ),
    },
}

NICHES = {
    "Tech / AI": {
        "softRange": "12-30s",
        "stakes": (
            "Disruption, obsolescence, breakthrough capability, competitive advantage, "
            "AI replacing humans, paradigm shifts"
        ),
        "tone": "Bold, precise, forward-looking. Clear insight or surprising claim about technology impact.",
        "preferredTypes": [
            "Zero-Second Claim", "Curiosity Gap", "Counterintuitive",
            "High Stakes Warning", "Live Proof",
        ],
    },
    "Finance": {
        "softRange": "15-35s",
        "stakes": (
            "Money lost/gained, hidden risk, wealth gap, market timing, financial ruin, "
            "generational wealth"
        ),
        "tone": "Risk/reward framing. Concrete numbers, specific dollar figures, market-moving events.",
        "preferredTypes": [
            "Fear-Based", "High Stakes Warning", "Direct Benefit",
            "Contrarian", "FOMO Setup",
        ],
    },
    "Fitness": {
        "softRange": "10-25s",
        "stakes": (
            "Wasted effort, transformation, body image, injury risk, health, discipline, myth-busting"
        ),
        "tone": "Clear result or myth-busting. Proof something works or they're doing it wrong.",
        "preferredTypes": [
            "Contrarian", "Direct Benefit", "Personal Transformation", "Counterintuitive",
        ],
    },
    "Relationships": {
        "softRange": "10-25s",
        "stakes": "Emotional pain, betrayal, vulnerability, connection, toxic patterns, self-sabotage",
        "tone": "Emotional tension. Raw honesty and personal stakes feel authentic.",
        "preferredTypes": [
            "Story-Based", "Pattern Interrupt", "Curiosity Gap", "Personal Transformation",
        ],
    },
    "Drama / Commentary": {
        "softRange": "12-30s",
        "stakes": (
            "Conflict, controversy, hypocrisy, public exposure, power dynamics, hidden motives, call-out"
        ),
        "tone": "Conflict or controversy. Viewers want to pick a side immediately.",
        "preferredTypes": [
            "Pattern Interrupt", "High Stakes Warning", "Zero-Second Claim", "Fear-Based",
        ],
    },
    "Entrepreneurship": {
        "softRange": "15-30s",
        "stakes": (
            "Business failure, hard-earned lessons, missed opportunity, scaling pain, "
            "costly mistakes, status, money left on table"
        ),
        "tone": (
            "Hard-earned insight or costly mistake. Authenticity and specificity beat generic advice."
        ),
        "preferredTypes": [
            "Story-Based", "High Stakes Warning", "Contrarian",
            "Personal Transformation", "Curiosity Gap",
        ],
    },
    "Podcast": {
        "softRange": "15-40s",
        "stakes": (
            "Insight reveal, surprising reframe, expert credibility, insider access, "
            "counterintuitive wisdom"
        ),
        "tone": (
            "Deep insight or surprising reframe from an expert. The viewer should feel they're "
            "hearing something they wouldn't get elsewhere."
        ),
        "preferredTypes": [
            "Curiosity Gap", "Counterintuitive", "Authority", "Story-Based", "Contrarian",
        ],
    },
    "Generic": {
        "softRange": "12-30s",
        "stakes": "Broad curiosity gap, universal emotion, surprising claim, unexpected fact",
        "tone": "Surprising, specific, and emotionally resonant. Works for any audience.",
        "preferredTypes": [
            "Curiosity Gap", "Counterintuitive", "Direct Benefit", "Story-Based",
        ],
    },
}

# Union of PRD (13) + engine (15) = 18 types
HOOK_TYPES = [
    "Curiosity Gap",
    "Direct Benefit",
    "Fear-Based",
    "Authority",
    "Contrarian",
    "Counterintuitive",
    "Story-Based",
    "Pattern Interrupt",
    "High Stakes Warning",
    "Social Proof",
    "Elimination",
    "Objection Handler",
    "Pain Escalation",
    "Personal Transformation",
    "Live Proof",
    "FOMO Setup",
    "Zero-Second Claim",
    "Extended Demo",
    "Identity Hook",
]

FUNNEL_ROLES = [
    "curiosity_opener",
    "pain_escalation",
    "solution_reveal",
    "proof_authority",
    "retention_hook",
    "extended_demo",
]

# 10-dimension holistic scoring used in hook evaluation prompts
SCORE_DIMENSIONS = [
    "scroll_stop",
    "curiosity_gap",
    "stakes_intensity",
    "emotional_voltage",
    "standalone_clarity",
    "thought_completeness",
    "click_through_likelihood",
    "linguistic_compression",
    "novelty_delta",
    "information_density",
]

# Regeneration fee tiers (confirmed by user)
REGEN_FEE_TIERS_INR = [
    (15 * 60, 1000),    # <=15min source video: Rs 10 (1000 paisa)
    (30 * 60, 1500),    # <=30min: Rs 15
    (60 * 60, 2000),    # <=60min: Rs 20
    (float("inf"), 2500),  # >60min: Rs 25
]
REGEN_FEE_USD_CENTS = 30  # Flat $0.30

# Single source of truth for the 17 base hook rules (A–Q).
# Imported by hook_identification.py (prompt building) and admin_service.py (DB seeding).
BASE_HOOK_RULES: dict[str, dict[str, str]] = {
    "A": {"title": "One topic per hook", "content": "One topic per hook \u2014 3+ topics = FAIL"},
    "B": {"title": "Contextual grounding", "content": "Contextual grounding \u2014 viewer must know WHO and WHY immediately"},
    "C": {"title": "Specificity serves one point only", "content": "Specificity serves one point only"},
    "D": {"title": "Character + proof arc", "content": "Character + proof arc (person + achievement in tight sequence)"},
    "E": {"title": "Let hook breathe", "content": "Let hook breathe \u2014 include follow-up sentences that complete the thought"},
    "F": {"title": "Urgency/FOMO framing", "content": "Urgency/FOMO framing (\"while you were sleeping...\")"},
    "G": {"title": "No generic claims without specific proof", "content": "No generic claims without specific proof"},
    "H": {"title": "Narrative escalation", "content": "Narrative escalation: intrigue\u2192proof\u2192escalation\u2192contrast\u2192open loop"},
    "I": {"title": "Composite hooks", "content": "Composite hooks: stitch non-contiguous segments for stronger arcs (mark as \"X:XX+Y:YY [composite]\")"},
    "J": {"title": "End at the landing", "content": "End at the landing \u2014 not before, not after"},
    "K": {"title": "Unresolved mechanism", "content": "Unresolved mechanism: viewer knows WHAT not HOW"},
    "L": {"title": "Pain escalation", "content": "Pain escalation: layer frustration (statement\u2192specifics\u2192vivid analogy)"},
    "M": {"title": "Elimination hooks", "content": "Elimination hooks: remove expected answers systematically"},
    "N": {"title": "Objection handling", "content": "Objection handling: catch viewers at bounce moment"},
    "O": {"title": "Funnel role diversity", "content": "Funnel role diversity: 5 hooks serve different purposes"},
    "P": {"title": "Strip section labels", "content": "Strip section labels/navigation text from hook starts"},
    "Q": {"title": "Workflow demos", "content": "Workflow demos: include full step-by-step sequence, don't cut mid-demo"},
}


def get_regen_fee(video_duration_seconds: float, currency: str) -> int:
    """Return regeneration fee in smallest currency unit (paisa/cents)."""
    if currency == "USD":
        return REGEN_FEE_USD_CENTS
    for max_duration, fee in REGEN_FEE_TIERS_INR:
        if video_duration_seconds <= max_duration:
            return fee
    return REGEN_FEE_TIERS_INR[-1][1]
