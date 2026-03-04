# Ported from hookcut_engine.jsx — source of truth for all LLM prompt construction.
# LANGUAGES: 13 entries (12 + Other) from hookcut_v4_prd3.jsx LANGUAGES config
# NICHES: 8 entries from hookcut_v4_prd3.jsx NICHES config
# HOOK_TYPES: 18 entries — union of PRD (13) + engine (15)
# FUNNEL_ROLES: 6 entries
# SCORE_DIMENSIONS: 7 entries (engine's holistic approach)

LANGUAGES = {
    "English": {
        "label": "English",
        "promptNote": (
            "LANGUAGE: English (possibly Indian English with Hinglish code-switching). "
            "Hindi words mixed into English are acceptable — do not reject hooks for code-switching."
        ),
    },
    "Hinglish": {
        "label": "Hinglish (Hindi + English)",
        "promptNote": (
            "LANGUAGE: Hinglish — a natural mix of Hindi and English common among Indian creators. "
            "Both languages flow within sentences. Output hook_text in the ORIGINAL mixed language "
            "exactly as spoken — NEVER normalize to pure English or pure Hindi."
        ),
    },
    "Hindi": {
        "label": "Hindi",
        "promptNote": (
            "LANGUAGE: Hindi (Devanagari or romanized). Code-switching to English for technical "
            "terms is normal. Output hook_text in the ORIGINAL Hindi — NEVER translate."
        ),
    },
    "Tamil": {
        "label": "Tamil",
        "promptNote": (
            "LANGUAGE: Tamil (or Tanglish — Tamil mixed with English). Code-switching to English "
            "is very common among Tamil tech/education creators. Output hook_text in the ORIGINAL "
            "language — NEVER translate."
        ),
    },
    "Telugu": {
        "label": "Telugu",
        "promptNote": (
            "LANGUAGE: Telugu (or Telugu mixed with English). Code-switching to English for "
            "technical terms is very common. Output hook_text in the ORIGINAL language — "
            "NEVER translate."
        ),
    },
    "Kannada": {
        "label": "Kannada",
        "promptNote": (
            "LANGUAGE: Kannada (or Kannada mixed with English). Code-switching is common. "
            "Output hook_text in the ORIGINAL language — NEVER translate."
        ),
    },
    "Malayalam": {
        "label": "Malayalam",
        "promptNote": (
            "LANGUAGE: Malayalam (or Manglish — Malayalam mixed with English). Code-switching "
            "is common. Output hook_text in the ORIGINAL language — NEVER translate."
        ),
    },
    "Marathi": {
        "label": "Marathi",
        "promptNote": (
            "LANGUAGE: Marathi (or Marathi mixed with English/Hindi). Code-switching is common. "
            "Output hook_text in the ORIGINAL language — NEVER translate."
        ),
    },
    "Gujarati": {
        "label": "Gujarati",
        "promptNote": (
            "LANGUAGE: Gujarati (or Gujarati mixed with English/Hindi). Code-switching is common "
            "especially in business/finance content. Output hook_text in the ORIGINAL language — "
            "NEVER translate."
        ),
    },
    "Punjabi": {
        "label": "Punjabi",
        "promptNote": (
            "LANGUAGE: Punjabi (Gurmukhi or romanized, or Punjabi mixed with English/Hindi). "
            "Code-switching is common. Output hook_text in the ORIGINAL language — NEVER translate."
        ),
    },
    "Bengali": {
        "label": "Bengali",
        "promptNote": (
            "LANGUAGE: Bengali (or Banglish — Bengali mixed with English). Code-switching is "
            "common. Output hook_text in the ORIGINAL language — NEVER translate."
        ),
    },
    "Odia": {
        "label": "Odia",
        "promptNote": (
            "LANGUAGE: Odia (or Odia mixed with English/Hindi). Code-switching is common. "
            "Output hook_text in the ORIGINAL language — NEVER translate."
        ),
    },
    "Other": {
        "label": "Other Language",
        "promptNote": (
            "LANGUAGE: Auto-detect from transcript. Code-switching to English or Hindi is normal "
            "for Indian creators. Apply all hook rules identically. Output hook_text in the "
            "ORIGINAL language — NEVER translate."
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
]

FUNNEL_ROLES = [
    "curiosity_opener",
    "pain_escalation",
    "solution_reveal",
    "proof_authority",
    "retention_hook",
    "extended_demo",
]

# Regeneration fee tiers (confirmed by user)
REGEN_FEE_TIERS_INR = [
    (15 * 60, 1000),    # <=15min source video: Rs 10 (1000 paisa)
    (30 * 60, 1500),    # <=30min: Rs 15
    (60 * 60, 2000),    # <=60min: Rs 20
    (float("inf"), 2500),  # >60min: Rs 25
]
REGEN_FEE_USD_CENTS = 30  # Flat $0.30


def get_regen_fee(video_duration_seconds: float, currency: str) -> int:
    """Return regeneration fee in smallest currency unit (paisa/cents)."""
    if currency == "USD":
        return REGEN_FEE_USD_CENTS
    for max_duration, fee in REGEN_FEE_TIERS_INR:
        if video_duration_seconds <= max_duration:
            return fee
    return REGEN_FEE_TIERS_INR[-1][1]
