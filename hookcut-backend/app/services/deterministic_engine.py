"""
Deterministic hook identification engine v4 — no LLM calls.

Uses word-boundary keyword matching, 15 viral hook templates,
7-dimension per-dimension scoring, temporal position weighting,
triple-combo bonus, sentence-level features (length, speech density),
numerical specificity detection, and hook boundary detection.

Scoring formula alignment (from expert training):
  0.20 * pattern_interrupt
  0.20 * curiosity_gap
  0.15 * direct_viewer_relevance
  0.15 * emotional_trigger
  0.10 * contrarian_statement
  0.10 * numerical_specificity
  0.10 * authority_signal

Admin-only: controlled by HOOK_ENGINE_MODE setting (stored in Redis).
"""

import re
import logging
from dataclasses import dataclass, field

from app.services.hook_engine import HookCandidate, HookEngineResult
from app.llm.prompts.constants import NICHES

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# WORD-BOUNDARY KEYWORD MATCHING
# ═══════════════════════════════════════════════════════════════════════════════
# All keywords are matched using word boundaries to prevent false positives
# (e.g., "but" should NOT match "butter", "stop" should NOT match "unstoppable").
# Multi-word phrases use substring match (safe — spaces prevent false hits).

def _compile_patterns(keywords: dict[str, float]) -> list[tuple[re.Pattern, float]]:
    """Compile keyword dict into (regex, weight) pairs for word-boundary matching."""
    patterns = []
    for kw, weight in keywords.items():
        if " " in kw:
            # Multi-word phrase: safe to use substring match
            patterns.append((re.compile(re.escape(kw), re.IGNORECASE), weight))
        else:
            # Single word: use word boundaries
            patterns.append((re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE), weight))
    return patterns


def _match_score(text: str, patterns: list[tuple[re.Pattern, float]]) -> float:
    """Sum weighted matches for a text against compiled patterns."""
    total = 0.0
    for pat, weight in patterns:
        if pat.search(text):
            total += weight
    return total


def _match_count(text: str, patterns: list[tuple[re.Pattern, float]]) -> int:
    """Count how many patterns match (unweighted)."""
    return sum(1 for pat, _ in patterns if pat.search(text))


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL KEYWORD DICTIONARIES (keyword → weight)
# ═══════════════════════════════════════════════════════════════════════════════

# --- Pattern Interrupt / Scroll Stop signals ---
IMPERATIVE_PATTERNS = _compile_patterns({
    "stop": 1.5, "wait": 1.5, "listen": 1.5, "watch": 1.0, "look": 1.0,
    "hold on": 2.0, "hold up": 2.0, "don't": 1.0, "never": 1.0,
    "stop what you're doing": 3.0, "forget everything": 3.0,
    "pay attention": 2.0, "think again": 2.0,
})

NEGATION_PATTERNS = _compile_patterns({
    "you're doing this wrong": 3.0, "don't do this": 2.5,
    "stop doing": 2.0, "you're making a mistake": 2.5,
    "this is wrong": 2.0, "you're wrong about": 2.5,
    "not what you think": 2.5, "you've been lied to": 3.0,
})

CONTRAST_PATTERNS = _compile_patterns({
    "everyone thinks": 2.5, "most people think": 2.5,
    "you think": 2.0, "they told you": 2.0,
    "you've been told": 2.5, "conventional wisdom": 2.0,
    "common advice": 2.0, "popular opinion": 2.0,
    "instead of": 1.5, "on the other hand": 1.5,
    "but actually": 2.5, "but the truth is": 3.0,
    "but here's the thing": 3.0, "but nobody": 2.5,
})

# --- Curiosity Gap signals ---
OPEN_LOOP_PATTERNS = _compile_patterns({
    "this is why": 2.5, "nobody tells you": 3.0,
    "here's the thing": 3.0, "the reason is": 2.5,
    "here's the trick": 3.0, "here's what": 2.5,
    "nobody talks about": 3.0, "what nobody mentions": 3.0,
    "they don't want you to know": 3.5, "bet you didn't know": 3.0,
    "what they don't tell you": 3.0, "the truth about": 2.5,
    "the real reason": 2.5, "ever wonder": 2.0,
    "here's why": 2.5, "the truth is": 2.5,
    "you won't believe": 2.5, "did you know": 2.0,
})

MYSTERY_PATTERNS = _compile_patterns({
    "secret": 2.0, "hidden": 2.0, "trick": 1.5,
    "little-known": 2.5, "little known": 2.5,
    "best kept secret": 3.0, "underground": 1.5,
    "behind the scenes": 2.0, "insider": 2.0,
})

# --- Stakes / Risk / Reward signals ---
RISK_PATTERNS = _compile_patterns({
    "mistake": 2.0, "danger": 2.0, "dangerous": 2.0,
    "ruin": 2.5, "ruined": 2.0, "lose": 1.5, "losing": 1.5,
    "fail": 1.5, "failure": 2.0, "destroy": 2.5,
    "waste": 1.5, "wasting": 1.5, "cost": 1.5,
    "risk": 1.5, "crash": 2.0, "broke": 1.5,
    "dead": 2.0, "kill": 1.5, "nightmare": 2.5,
    "devastating": 2.5, "lost everything": 3.0,
    "biggest mistake": 3.0, "almost died": 3.0,
    "saved my": 2.0, "warning": 2.0,
})

REWARD_PATTERNS = _compile_patterns({
    "hack": 1.5, "strategy": 1.5, "growth": 1.5,
    "money": 1.5, "revenue": 1.5, "income": 1.5,
    "profit": 1.5, "success": 1.5, "opportunity": 1.5,
    "unlock": 2.0, "double": 1.5, "triple": 1.5,
    "million": 2.0, "scale": 1.5, "shortcut": 2.0,
    "formula": 2.0, "blueprint": 2.0, "framework": 1.5,
    "cheat code": 2.5, "game changer": 2.5,
    "breakthrough": 2.5, "changed my life": 3.0,
    "life changing": 2.5, "everything changed": 3.0,
})

# --- Authority signals ---
AUTHORITY_PATTERNS = _compile_patterns({
    "research shows": 2.5, "studies show": 2.5,
    "according to": 2.0, "scientifically proven": 3.0,
    "published in": 2.5, "after 10 years": 3.0,
    "i've spent": 2.0, "having done": 2.0,
    "years of experience": 2.5, "in my career": 2.0,
    "i analyzed": 2.5, "harvard": 2.0, "stanford": 2.0,
    "expert": 1.5, "data shows": 2.0,
})

# --- Identity / Viewer Relevance signals ---
IDENTITY_PATTERNS = _compile_patterns({
    "if you're a": 3.0, "as a creator": 2.5,
    "as a founder": 2.5, "as a developer": 2.5,
    "as an entrepreneur": 2.5, "for entrepreneurs": 2.5,
    "for creators": 2.5, "for beginners": 2.0,
    "if you're doing this": 3.0, "if you want": 2.0,
    "if you're posting": 3.0, "if you're struggling": 3.0,
    "if you're trying": 2.5, "if you've been": 2.5,
})

# --- Story signals ---
STORY_PATTERNS = _compile_patterns({
    "i was": 1.0, "i used to": 1.5, "when i": 1.0,
    "years ago": 1.5, "one day": 1.5, "true story": 2.5,
    "this happened to me": 2.5, "i'll never forget": 3.0,
    "that's when i realized": 3.0, "let me tell you": 2.0,
    "suddenly": 1.5, "out of nowhere": 2.0,
    "looking back": 1.5, "the moment": 1.5,
})

# --- Direct Benefit signals ---
BENEFIT_PATTERNS = _compile_patterns({
    "step by step": 2.5, "how to": 2.0, "in just": 2.0,
    "the only way": 2.5, "guaranteed": 2.0, "exact method": 2.5,
    "simple trick": 2.0, "easy way": 1.5, "method": 1.0,
    "technique": 1.0, "template": 1.5,
    "instantly": 1.5, "immediately": 1.5,
})

# --- Absolute / intensity signals ---
ABSOLUTE_PATTERNS = _compile_patterns({
    "always": 1.5, "never": 1.5, "everyone": 1.5,
    "nobody": 1.5, "every single": 2.0, "zero": 1.0,
    "nothing": 1.0, "everything": 1.5, "absolutely": 1.5,
    "completely": 1.5, "literally": 1.0, "insane": 1.5,
    "incredible": 1.5, "unbelievable": 2.0, "mind-blowing": 2.5,
    "jaw-dropping": 2.5, "terrifying": 2.0, "wild": 1.0,
})

# --- Filler / Sponsor signals (for rejection) ---
FILLER_PATTERNS = _compile_patterns({
    "subscribe": 1.0, "like button": 1.0, "hit the bell": 1.0,
    "comment below": 1.0, "share this": 1.0, "follow me": 1.0,
    "link in description": 1.0, "link in the description": 1.0,
    "sponsor": 1.0, "brought to you by": 1.0,
    "hello everyone": 1.0, "hey guys": 1.0, "what's up": 1.0,
    "welcome back": 1.0, "thanks for watching": 1.0,
    "see you next": 1.0, "make sure to": 1.0,
    "don't forget to subscribe": 1.0, "smash that": 1.0,
    "ring that bell": 1.0, "this video is sponsored": 1.0,
    "today's sponsor": 1.0, "use code": 1.0,
    "use my link": 1.0, "promo code": 1.0,
})

# --- Numerical Specificity signals ---
NUMERICAL_PATTERNS = _compile_patterns({
    "3 things": 2.0, "5 things": 2.0, "7 things": 2.0, "10 things": 2.0,
    "3 steps": 2.0, "5 steps": 2.0, "7 steps": 2.0, "10 steps": 2.0,
    "3 ways": 2.0, "5 ways": 2.0, "7 ways": 2.0, "10 ways": 2.0,
    "3 reasons": 2.0, "5 reasons": 2.0, "7 reasons": 2.0,
    "3 mistakes": 2.5, "5 mistakes": 2.5,
    "3 secrets": 2.5, "5 secrets": 2.5,
    "30 days": 1.5, "90 days": 1.5, "24 hours": 1.5,
})
# Regex for inline numbers (percentages, multipliers, dollar amounts)
_NUM_RE = re.compile(r'\b\d+%|\b\d+[xX]\b|\$[\d,]+[kKmMbB]?|\b\d+[kKmMbB]\b')

# --- Direct Viewer Relevance (you/your counting) ---
_YOU_RE = re.compile(r"\byou(?:'re|r|rself)?\b", re.IGNORECASE)
_IF_YOU_RE = re.compile(r"\bif you(?:'re|r)?\b", re.IGNORECASE)
_WHEN_YOU_RE = re.compile(r"\bwhen you\b", re.IGNORECASE)

# --- 15 Viral Hook Templates (bonus scoring) ---
# Each template is a (regex, template_name, bonus) tuple
HOOK_TEMPLATES: list[tuple[re.Pattern, str, float]] = [
    (re.compile(r"you'?re\s+(?:making|doing)\s+(?:this|these|a)\s+mistake", re.I), "Mistake Hook", 2.0),
    (re.compile(r"(?:everyone|most people)\s+(?:thinks?|believes?|says?)\b.*(?:wrong|doesn't|don't|isn't)", re.I), "Contrarian Hook", 2.0),
    (re.compile(r"nobody\s+(?:talks?|tells?|mentions?)\s+(?:about)?\b", re.I), "Curiosity Gap Hook", 2.0),
    (re.compile(r"(?:i\s+)?(?:analyzed?|studied|researched?)\s+\d+", re.I), "Authority Hook", 2.0),
    (re.compile(r"if\s+you'?re\s+(?:\w+\s+){0,4}(?:and|but)\s+(?:not|aren't|can't)", re.I), "If-You Hook", 2.0),
    (re.compile(r"(?:the\s+)?(?:rule|thing)\s+nobody\s+tells\s+you", re.I), "Hidden Rule Hook", 2.0),
    (re.compile(r"^(?:stop|wait|hold on|listen)\b", re.I), "Pattern Interrupt Hook", 1.5),
    (re.compile(r"\b\d+%\s+of\s+(?:people|creators?|businesses?|videos?)\s+(?:fail|don't|never)", re.I), "Shocking Statistic Hook", 2.0),
    (re.compile(r"this\s+(?:will|is\s+going\s+to)\s+change\s+(?:how|the\s+way)\s+you", re.I), "Outcome Hook", 1.5),
    (re.compile(r"(?:this\s+is|you'?re)\s+(?:killing|destroying|ruining)\s+your", re.I), "Fear Hook", 2.0),
    (re.compile(r"^why\s+(?:do|does|are|is|don't|doesn't)\b", re.I), "Curiosity Question Hook", 1.5),
    (re.compile(r"here'?s?\s+(?:the\s+)?(?:trick|secret|hack|formula)", re.I), "Reveal Hook", 1.5),
    (re.compile(r"how\s+to\s+\w+.*\bin\s+\d+\s+(?:days?|minutes?|seconds?|hours?|steps?)", re.I), "Direct Benefit Hook", 2.0),
    (re.compile(r"(?:the\s+)?(?:algorithm|secret|hidden)\s+(?:secret|trick|hack|formula)", re.I), "Secret Hook", 1.5),
    (re.compile(r"(?:\d+\s+)?(?:months?|years?|weeks?)\s+ago\s+(?:i|we|my)", re.I), "Story Hook", 1.5),
]


def _template_bonus(text: str) -> float:
    """Check text against 15 viral hook templates. Return max bonus."""
    best = 0.0
    for pat, _name, bonus in HOOK_TEMPLATES:
        if pat.search(text):
            best = max(best, bonus)
    return best


# ═══════════════════════════════════════════════════════════════════════════════
# 12 HOOK TEMPLATE GRAMMAR (structural pattern detection)
# ═══════════════════════════════════════════════════════════════════════════════
# Detects the underlying narrative structure, not exact phrases.
# E.g., "expectation + contrast_connector + contradiction" catches hundreds
# of hook variations from a single rule.

# Component detectors (reusable across templates)
_BELIEF_PHRASES = re.compile(
    r"\b(?:most people (?:think|believe|assume)|everyone (?:thinks|believes|says)|"
    r"you (?:might|would|probably) (?:think|expect|assume)|"
    r"we (?:usually|tend to|often) (?:think|believe|assume)|"
    r"(?:it seems|it looks) (?:like|obvious)|"
    r"(?:in school|we've been taught|commonly|traditionally))\b", re.I,
)
_CONTRAST_CONNECTORS = re.compile(
    r"\b(?:but|however|actually|turns out|yet|except|in reality)\b", re.I,
)
_CONTRADICTION_PHRASES = re.compile(
    r"(?:not (?:true|correct|right|how)|wrong|false|incorrect|"
    r"doesn't work|isn't (?:true|correct|right)|that's (?:not|wrong))", re.I,
)
_ANOMALY_PHRASES = re.compile(
    r"\b(?:strange|weird|surprising|unexpected|remarkable|peculiar|"
    r"fascinating|bizarre|mysterious|puzzling)\b", re.I,
)
_HIDDEN_CAUSE_PHRASES = re.compile(
    r"(?:(?:the )?(?:real|hidden|true|actual) (?:reason|cause|factor|explanation)|"
    r"there's (?:a|one) (?:hidden|secret) (?:factor|reason|rule))", re.I,
)
_DISCOVERY_PHRASES = re.compile(
    r"(?:(?:researchers?|scientists?|we) (?:discovered|found|realized)|"
    r"(?:the )?(?:answer|key|insight|discovery) (?:turns out|is|was)|"
    r"once you understand|everything changes)", re.I,
)
_PARADOX_PHRASES = re.compile(
    r"(?:the more .{3,30} the (?:less|worse|more)|"
    r"(?:shouldn't|can't|wouldn't) .{3,20} but (?:it )?(?:does|did|can))", re.I,
)
_RULE_PHRASES = re.compile(
    r"(?:(?:there's )?(?:one|a) (?:rule|principle|factor|thing) that (?:determines?|controls?)|"
    r"(?:the )?(?:number one|single biggest|most important) (?:rule|factor|thing))", re.I,
)


def _detect_grammar_templates(text: str) -> list[tuple[str, float]]:
    """Detect which of the 12 hook grammar templates match.

    Returns list of (template_name, bonus_score) for all matches.
    """
    matches: list[tuple[str, float]] = []
    text_lower = text.lower()

    # 1. Expectation → Contradiction (most common: ~30%)
    if _BELIEF_PHRASES.search(text) and _CONTRAST_CONNECTORS.search(text):
        matches.append(("expectation_contradiction", 2.5))

    # 2. Observation → Mystery
    if _ANOMALY_PHRASES.search(text) and ("?" in text or "about" in text_lower):
        matches.append(("observation_mystery", 2.0))

    # 3. Problem → Stakes
    if (_match_count(text, RISK_PATTERNS) > 0
        and (_YOU_RE.search(text) or "most" in text_lower or "people" in text_lower)):
        matches.append(("problem_stakes", 1.8))

    # 4. Hidden Cause
    if _HIDDEN_CAUSE_PHRASES.search(text):
        matches.append(("hidden_cause", 2.0))

    # 5. Counterintuitive Fact
    if _BELIEF_PHRASES.search(text) and _CONTRADICTION_PHRASES.search(text):
        matches.append(("counterintuitive_fact", 2.5))

    # 6. Story Setup
    if (re.search(r"\b\d+\s+(?:months?|years?|weeks?|days?)\s+ago\b", text, re.I)
        and re.search(r"\bi\b", text_lower)):
        matches.append(("story_setup", 1.5))

    # 7. Authority Insight
    if (_match_count(text, AUTHORITY_PATTERNS) > 0
        and (_DISCOVERY_PHRASES.search(text) or _ANOMALY_PHRASES.search(text))):
        matches.append(("authority_insight", 2.0))

    # 8. Question Hook
    if "?" in text and len(text.split()) >= 5:
        if re.search(r"\b(?:why|how|what)\b", text_lower):
            matches.append(("question_hook", 1.5))

    # 9. Rule Revelation
    if _RULE_PHRASES.search(text):
        matches.append(("rule_revelation", 2.0))

    # 10. Consequence Warning
    if (re.search(r"\b(?:will|is going to|can)\b", text_lower)
        and _match_count(text, RISK_PATTERNS) > 0
        and _YOU_RE.search(text)):
        matches.append(("consequence_warning", 1.8))

    # 11. Paradox Hook
    if _PARADOX_PHRASES.search(text):
        matches.append(("paradox_hook", 2.5))

    # 12. Resolution Promise
    if re.search(r"\bto understand\b", text_lower) or re.search(r"\blet's look at\b", text_lower):
        if _match_count(text, EXPLANATION_PATTERNS) == 0:  # not yet explaining
            matches.append(("resolution_promise", 1.0))

    return matches


def _grammar_bonus(text: str) -> float:
    """Compute bonus from hook template grammar matches.
    Returns the sum of top 2 template bonuses (hooks often combine templates)."""
    matches = _detect_grammar_templates(text)
    if not matches:
        return 0.0
    # Sort by score descending, take top 2 (hooks often combine 2-3 patterns)
    scores = sorted([s for _, s in matches], reverse=True)
    return scores[0] + (scores[1] * 0.5 if len(scores) > 1 else 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSCRIPT NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════════
# Clean speech disfluencies and filler before analysis.

_DISFLUENCY_RE = re.compile(
    r"\b(?:um+|uh+|ah+|er+|like,?\s+(?=like)|you know,?\s+(?=you know)|"
    r"i mean,?\s+(?=i mean)|sort of,?\s+(?=sort of)|kind of,?\s+(?=kind of))\b",
    re.IGNORECASE,
)
_REPEATED_WORDS_RE = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)


def _normalize_transcript(text: str) -> str:
    """Remove speech disfluencies and repeated words for cleaner signal detection."""
    text = _DISFLUENCY_RE.sub("", text)
    text = _REPEATED_WORDS_RE.sub(r"\1", text)
    # Collapse multiple spaces
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


# --- Discovery / Insight signals (knowledge reward anticipation) ---
DISCOVERY_PATTERNS = _compile_patterns({
    "what researchers discovered": 2.5, "after studying": 2.0,
    "the answer turns out": 2.5, "once you understand": 2.5,
    "everything changes": 2.0, "the key insight": 2.5,
    "we found something": 2.0, "something unexpected": 2.0,
    "much simpler than you think": 2.5, "much harder than": 2.0,
    "what we discovered": 2.5, "this changes everything": 2.5,
    "the breakthrough": 2.5,
})

# --- Conceptual Tension / Misconception signals (for lecture/explainer hooks) ---
CONCEPTUAL_TENSION_PATTERNS = _compile_patterns({
    "counterintuitive": 2.5, "paradox": 2.5, "unexpected": 2.0,
    "strange": 1.5, "weird": 1.5, "bizarre": 2.0,
    "doesn't make sense": 2.5, "hard to believe": 2.0,
    "seems impossible": 2.5, "defies logic": 2.5,
    "the weird thing": 2.5, "the strange thing": 2.5,
})

MISCONCEPTION_PATTERNS = _compile_patterns({
    "most people think": 2.5, "most textbooks": 2.5,
    "commonly believed": 2.5, "popular misconception": 3.0,
    "you probably think": 2.5, "we've been taught": 2.5,
    "completely wrong": 3.0, "actually wrong": 2.5,
    "not how it works": 2.5, "doesn't work that way": 2.5,
    "explain this incorrectly": 3.0, "misunderstand": 2.0,
    "the way we imagine": 2.0, "picture is wrong": 2.5,
})

# --- Hook Boundary / Explanation markers (signal hook END) ---
EXPLANATION_PATTERNS = _compile_patterns({
    "so here's how": 2.0, "let me show you": 2.0,
    "let me explain": 2.0, "the way it works": 2.0,
    "step one": 1.5, "first of all": 1.5,
    "basically": 1.0, "essentially": 1.0,
    "in other words": 1.5, "what i mean is": 1.5,
    "so the first thing": 1.5, "the answer is": 2.0,
    "here's how you do it": 2.0, "let me break it down": 2.0,
    "so what you need to do": 2.0,
    # Lecture-specific boundaries
    "let's break this down": 2.0, "so what is": 1.5,
    "is defined as": 2.0, "refers to": 1.5,
    "watch what happens": 1.5, "there are three": 1.5,
    "there are two": 1.5, "there are four": 1.5,
    "so let's look at": 2.0, "let's look at how": 2.0,
})

# --- Transition phrases (signal hook END → explanation begins) ---
TRANSITION_PATTERNS = _compile_patterns({
    "so": 0.5, "because": 0.5, "the way": 0.5,
    "now let me": 1.0, "so let's": 1.0,
    "okay so": 1.0, "alright so": 1.0,
    "with that said": 1.0, "moving on": 1.0,
})


# ═══════════════════════════════════════════════════════════════════════════════
# NARRATIVE PHASE DETECTION (replaces fixed duration rules)
# ═══════════════════════════════════════════════════════════════════════════════
# Hook = narrative buildup before knowledge delivery.
# Track 4 phases: problem → stakes → curiosity_gap → outcome_tease
# Hook ends when the narrative arc completes (all phases present)
# OR when an explanation boundary is hit.

def _narrative_completion_score(text: str) -> float:
    """Score how complete the narrative tension arc is (0-5).

    Two models merged:
    1. Short-form: problem → stakes → curiosity → outcome_tease
    2. Curiosity Escalation (educational/lecture):
       observation → expectation → contradiction → escalated_mystery → knowledge_promise

    Returns max of both models (a segment may match either pattern).
    """
    text_lower = text.lower()

    # ── Model A: Short-form hook arc (0-4) ──
    a = 0.0
    # Problem present
    if (_match_count(text, NEGATION_PATTERNS) > 0
        or _match_count(text, MISCONCEPTION_PATTERNS) > 0
        or _match_count(text, RISK_PATTERNS) > 0
        or any(p in text_lower for p in ["the problem", "the issue", "what's wrong", "struggle"])):
        a += 1.0
    # Stakes present
    if (_match_count(text, RISK_PATTERNS) > 0
        or _match_count(text, REWARD_PATTERNS) > 0
        or _match_count(text, ABSOLUTE_PATTERNS) > 0):
        a += 1.0
    # Curiosity gap present
    if (_match_count(text, OPEN_LOOP_PATTERNS) > 0
        or _match_count(text, MYSTERY_PATTERNS) > 0
        or _match_count(text, CONCEPTUAL_TENSION_PATTERNS) > 0
        or "?" in text):
        a += 1.0
    # Outcome tease
    if any(p in text_lower for p in [
        "changes the way", "changes how", "will change",
        "understanding why", "that's why", "and that's",
        "the key is", "turns out", "it turns out",
    ]):
        a += 1.0

    # ── Model B: 5-Stage Curiosity Escalation (educational/lecture) (0-5) ──
    b = 0.0
    # Stage 1: Intriguing observation (anomaly/surprise words)
    if (_match_count(text, CONCEPTUAL_TENSION_PATTERNS) > 0
        or any(w in text_lower for w in [
            "strange", "weird", "interesting", "surprising",
            "unexpected", "remarkable", "peculiar", "fascinating",
        ])):
        b += 1.0
    # Stage 2: Intuitive expectation (common belief framing)
    if any(p in text_lower for p in [
        "most people think", "most people imagine", "you might expect",
        "it seems obvious", "you probably think", "we tend to think",
        "the common view", "we've been taught", "you might assume",
        "the way we imagine", "picture a", "imagine a",
    ]):
        b += 1.0
    # Stage 3: Contradiction (belief invalidation)
    if any(p in text_lower for p in [
        "but that's not", "but actually", "but it turns out",
        "however", "that's not true", "that's not how",
        "completely wrong", "actually wrong", "not actually",
        "but the truth", "but in reality",
    ]):
        b += 1.0
    # Stage 4: Escalated mystery (deeper anomaly)
    if any(p in text_lower for p in [
        "in fact", "even stranger", "the real mystery",
        "even more surprising", "what's really happening",
        "it gets worse", "it gets stranger", "the deeper issue",
        "and it gets", "not only that",
    ]):
        b += 1.0
    # Stage 5: Knowledge promise (explanation teaser)
    if any(p in text_lower for p in [
        "to understand this", "to understand why",
        "let's look at", "here's what's actually",
        "so how does", "so why does", "so what happens",
        "the answer lies in", "the explanation is",
    ]):
        b += 1.0

    # Return the higher of both models (normalized to same scale)
    return max(a, b * 0.8)  # Scale B to 0-4 range for consistency


# ═══════════════════════════════════════════════════════════════════════════════
# HOOK TYPE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def _classify_hook_type(
    scroll_stop: float, curiosity_gap: float, stakes: float,
    emotional: float, text: str,
    authority_score: float, story_score: float, benefit_score: float,
) -> tuple[str, str]:
    """Classify into one of the 18 HOOK_TYPES and assign a funnel_role."""
    text_lower = text.lower()

    # Score each type based on signals
    type_scores: dict[str, float] = {}

    # Pattern Interrupt: high scroll_stop
    type_scores["Pattern Interrupt"] = scroll_stop * 0.8
    # Curiosity Gap: high curiosity
    type_scores["Curiosity Gap"] = curiosity_gap * 0.9
    # High Stakes Warning: high stakes
    type_scores["High Stakes Warning"] = stakes * 0.85
    # Fear-Based: risk language dominant
    type_scores["Fear-Based"] = _match_score(text, RISK_PATTERNS) * 0.6
    # Authority: authority signals
    type_scores["Authority"] = authority_score * 0.7
    # Story-Based: story signals
    type_scores["Story-Based"] = story_score * 0.7
    # Direct Benefit: benefit signals
    type_scores["Direct Benefit"] = benefit_score * 0.7
    # Contrarian: contrast patterns
    type_scores["Contrarian"] = _match_score(text, CONTRAST_PATTERNS) * 0.6
    # Counterintuitive: contrast + negation
    type_scores["Counterintuitive"] = (
        _match_score(text, CONTRAST_PATTERNS) * 0.4
        + _match_score(text, NEGATION_PATTERNS) * 0.4
    )
    # Personal Transformation: story + reward
    type_scores["Personal Transformation"] = (
        story_score * 0.3 + _match_score(text, REWARD_PATTERNS) * 0.3
    )
    # FOMO Setup: urgency + reward
    if any(w in text_lower for w in ["before it's too late", "running out", "last chance", "limited"]):
        type_scores["FOMO Setup"] = 5.0
    # Zero-Second Claim: strong claim in first clause
    if _match_score(text, ABSOLUTE_PATTERNS) > 2.0 and stakes > 4.0:
        type_scores["Zero-Second Claim"] = stakes * 0.7
    # Social Proof: numbers + authority
    if re.search(r'\b\d+[kmb]?\+?\s*(people|users|subscribers|followers|views)', text_lower):
        type_scores["Social Proof"] = 5.0 + authority_score * 0.3
    # Pain Escalation: layered risk
    type_scores["Pain Escalation"] = _match_score(text, RISK_PATTERNS) * 0.4 + emotional * 0.2

    # Pick the highest-scoring type
    best_type = max(type_scores, key=type_scores.get)
    if type_scores[best_type] < 1.0:
        best_type = "Curiosity Gap"  # safe default

    # Assign funnel role
    FUNNEL_MAP = {
        "Curiosity Gap": "curiosity_opener",
        "Pattern Interrupt": "curiosity_opener",
        "Contrarian": "curiosity_opener",
        "Counterintuitive": "curiosity_opener",
        "Zero-Second Claim": "curiosity_opener",
        "FOMO Setup": "curiosity_opener",
        "High Stakes Warning": "pain_escalation",
        "Fear-Based": "pain_escalation",
        "Pain Escalation": "pain_escalation",
        "Direct Benefit": "solution_reveal",
        "Objection Handler": "solution_reveal",
        "Authority": "proof_authority",
        "Social Proof": "proof_authority",
        "Live Proof": "proof_authority",
        "Story-Based": "retention_hook",
        "Personal Transformation": "retention_hook",
        "Elimination": "retention_hook",
        "Extended Demo": "extended_demo",
    }
    funnel = FUNNEL_MAP.get(best_type, "curiosity_opener")
    return best_type, funnel


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSCRIPT PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_transcript_segments(transcript: str) -> list[dict]:
    """Parse transcript into timed segments with proper sentence-level granularity."""
    segments: list[dict] = []

    # Try timestamped format: [0:00] or 0:00
    ts_pattern = re.compile(
        r'(?:\[)?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*(.*?)(?=(?:\[)?\d{1,2}:\d{2}|\Z)',
        re.DOTALL,
    )
    matches = list(ts_pattern.finditer(transcript))

    if len(matches) >= 5:
        # Timestamped transcript
        raw = []
        for m in matches:
            ts_str = m.group(1)
            text = m.group(2).strip()
            if not text:
                continue
            parts = ts_str.split(":")
            if len(parts) == 2:
                secs = int(parts[0]) * 60 + int(parts[1])
            else:
                secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            raw.append({"start": float(secs), "text": text})

        # Merge tiny fragments (< 4 words) into preceding segment
        merged: list[dict] = []
        for seg in raw:
            if merged and len(seg["text"].split()) < 4:
                merged[-1]["text"] += " " + seg["text"]
            else:
                merged.append(dict(seg))

        # Individual segments
        segments.extend(merged)

        # Sliding windows of 2 adjacent segments for richer context
        for i in range(len(merged) - 1):
            segments.append({
                "start": merged[i]["start"],
                "text": merged[i]["text"] + " " + merged[i + 1]["text"],
            })

        # Windows of 3 for even broader context
        for i in range(len(merged) - 2):
            segments.append({
                "start": merged[i]["start"],
                "text": merged[i]["text"] + " " + merged[i + 1]["text"] + " " + merged[i + 2]["text"],
            })

    else:
        # Plain text: split by sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', transcript)
        if len(sentences) < 3:
            sentences = [s.strip() for s in transcript.split("\n") if s.strip()]
        if len(sentences) < 3:
            sentences = [s.strip() for s in re.split(r'[,;]', transcript) if len(s.strip()) > 10]

        total_chars = max(len(transcript), 1)

        def _est_time(chunk: str) -> float:
            pos = transcript.find(chunk[:50]) if len(chunk) >= 50 else transcript.find(chunk)
            if pos < 0:
                pos = 0
            # ~150 words/min ≈ 750 chars/min
            return (pos / total_chars) * (total_chars / 750) * 60

        # Individual sentences (8+ words)
        for s in sentences:
            s = s.strip()
            if len(s.split()) >= 6:
                segments.append({"start": _est_time(s), "text": s})

        # Windows of 2
        for i in range(len(sentences) - 1):
            chunk = sentences[i].strip() + " " + sentences[i + 1].strip()
            if len(chunk.split()) >= 8:
                segments.append({"start": _est_time(chunk), "text": chunk})

        # Windows of 3
        for i in range(len(sentences) - 2):
            chunk = " ".join(s.strip() for s in sentences[i:i + 3])
            if 10 <= len(chunk.split()) <= 60:
                segments.append({"start": _est_time(chunk), "text": chunk})

    # Compute end times
    # Sort by start time for end-time calculation
    segments.sort(key=lambda s: s["start"])
    for i, seg in enumerate(segments):
        if i + 1 < len(segments):
            seg["end"] = segments[i + 1]["start"]
        else:
            seg["end"] = seg["start"] + 30.0
        # Minimum 5s duration
        if seg["end"] - seg["start"] < 5:
            seg["end"] = seg["start"] + 15.0

    return segments


def _detect_hook_end(text: str) -> int | None:
    """Find where the hook ends within text (index of explanation start).
    Returns character index or None if no boundary found."""
    text_lower = text.lower()

    # Look for explanation/transition markers
    for pat, _ in EXPLANATION_PATTERNS:
        m = pat.search(text_lower)
        if m and m.start() > 20:  # Must be after some hook content
            return m.start()

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 7-DIMENSION SCORING (per dimension, not global)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class _DimensionScores:
    scroll_stop: float = 0.0
    curiosity_gap: float = 0.0
    stakes_intensity: float = 0.0
    emotional_voltage: float = 0.0
    standalone_clarity: float = 5.0  # neutral default
    thematic_focus: float = 5.0     # neutral default
    thought_completeness: float = 0.0


def _score_dimensions(text: str) -> _DimensionScores:
    """Score each dimension independently based on specific signal patterns."""
    scores = _DimensionScores()
    text_lower = text.lower()
    words = text.split()
    word_count = len(words)

    # ─── D1: scroll_stop (Pattern Interrupt Power) ───
    d1 = 0.0
    # Imperative opening
    if words and words[0].lower().rstrip(".,!?") in (
        "stop", "wait", "listen", "watch", "look", "don't", "never", "imagine"
    ):
        d1 += 3.0
    d1 += min(_match_score(text, IMPERATIVE_PATTERNS), 4.0)
    # Short first sentence (≤ 5 words)
    first_sent = re.split(r'[.!?]', text)[0]
    if len(first_sent.split()) <= 5 and len(first_sent.split()) >= 2:
        d1 += 2.5
    # Contrast structure
    d1 += min(_match_score(text, CONTRAST_PATTERNS) * 0.4, 2.0)
    # Question opening
    if "?" in text[:80]:
        d1 += 1.5
    # Negation framing
    d1 += min(_match_score(text, NEGATION_PATTERNS) * 0.4, 2.0)
    scores.scroll_stop = min(d1, 10.0)

    # ─── D2: curiosity_gap ───
    d2 = 0.0
    d2 += min(_match_score(text, OPEN_LOOP_PATTERNS), 5.0)
    d2 += min(_match_score(text, MYSTERY_PATTERNS), 3.0)
    d2 += min(_match_score(text, DISCOVERY_PATTERNS) * 0.4, 2.0)
    # Incomplete causal chain: "because"/"reason" without resolution
    if re.search(r'\b(because|reason|why)\b', text_lower):
        # Check if explanation follows within the segment
        causal_match = re.search(r'\b(because|reason|why)\b', text_lower)
        if causal_match and len(text) - causal_match.end() < 40:
            d2 += 2.0  # Causal word near end = unresolved
    # Ends mid-sentence or with ellipsis
    if text.rstrip().endswith("...") or text.rstrip().endswith("…"):
        d2 += 1.5
    # Question without answer in segment
    if "?" in text and not any(a in text_lower for a in ["the answer is", "it's because", "that's why"]):
        d2 += 1.0
    scores.curiosity_gap = min(d2, 10.0)

    # ─── D3: stakes_intensity ───
    d3 = 0.0
    d3 += min(_match_score(text, RISK_PATTERNS), 6.0)
    d3 += min(_match_score(text, REWARD_PATTERNS), 4.5)
    # Numerical outcomes ($X, X%, Xk)
    if re.search(r'\$[\d,]+|\d+%|\d+[xX]\b|\d+[kKmMbB]\b', text):
        d3 += 1.5
    # Absolute language
    d3 += min(_match_score(text, ABSOLUTE_PATTERNS) * 0.3, 1.5)
    scores.stakes_intensity = min(d3, 10.0)

    # ─── D4: emotional_voltage ───
    d4 = 0.0
    # Identity targeting
    d4 += min(_match_score(text, IDENTITY_PATTERNS), 4.0)
    # Authority statements
    d4 += min(_match_score(text, AUTHORITY_PATTERNS) * 0.5, 3.0)
    # Direct address: count "you/your/you're"
    you_count = len(_YOU_RE.findall(text))
    d4 += min(you_count * 1.0, 3.0)
    # "If you're..." / "When you..." — strongest viewer relevance
    if_you_count = len(_IF_YOU_RE.findall(text))
    when_you_count = len(_WHEN_YOU_RE.findall(text))
    d4 += min((if_you_count + when_you_count) * 1.5, 3.0)
    # Fear framing (risk + "you")
    if _match_count(text, RISK_PATTERNS) > 0 and you_count > 0:
        d4 += 1.5
    # Exclamatory tone
    if "!" in text:
        d4 += 0.5
    scores.emotional_voltage = min(d4, 10.0)

    # ─── D5: standalone_clarity ───
    d5 = 5.0  # neutral default
    # Complete sentence
    if re.search(r'[.!?]\s*$', text.strip()):
        d5 += 2.0
    # Unresolved pronouns at start ("It", "This", "That" as first word)
    first_word = words[0].lower().rstrip(".,!?'\"") if words else ""
    if first_word in ("it", "this", "that", "these", "those"):
        d5 -= 2.0
    # Mid-conversation entry markers
    if first_word in ("and", "but", "so", "also", "then", "plus"):
        d5 -= 1.5
    # Back-reference phrases
    if any(p in text_lower for p in ["like i said", "as i mentioned", "going back to", "as we discussed"]):
        d5 -= 1.5
    # Has own subject + verb (crude check: has at least 2 content words before a verb-like word)
    if word_count >= 5:
        d5 += 1.0
    scores.standalone_clarity = max(0.0, min(10.0, d5))

    # ─── D6: thematic_focus ───
    # Fewer unique words relative to total = more focused
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                 "have", "has", "had", "do", "does", "did", "will", "would", "could",
                 "should", "may", "might", "can", "shall", "to", "of", "in", "for",
                 "on", "with", "at", "by", "from", "as", "into", "through", "during",
                 "and", "or", "but", "if", "then", "that", "this", "it", "i", "you",
                 "we", "they", "he", "she", "my", "your", "his", "her", "our", "their",
                 "me", "him", "us", "them", "not", "no", "so", "just", "very", "really",
                 "about", "up", "out", "all", "more", "than", "what", "when", "how",
                 "who", "which", "where", "there", "here"}
    content_words = [w.lower().strip(".,!?;:'\"") for w in words if w.lower().strip(".,!?;:'\"") not in stopwords and len(w) > 2]
    if len(content_words) >= 3:
        unique = len(set(content_words))
        total = len(content_words)
        density = unique / total  # 0.3-1.0
        d6 = 10.0 - (density - 0.3) * 14.0  # 0.3→10, 1.0→0.2
        scores.thematic_focus = max(1.0, min(10.0, d6))
    else:
        scores.thematic_focus = 5.0

    # ─── D7: thought_completeness ───
    d7 = 0.0
    # Contains both a claim AND a stake
    has_claim = word_count >= 5  # at least a sentence fragment
    has_stake = _match_count(text, RISK_PATTERNS) > 0 or _match_count(text, REWARD_PATTERNS) > 0
    if has_claim and has_stake:
        d7 += 4.0
    # Complete question
    if "?" in text and word_count >= 5:
        d7 += 3.0
    # Ends at natural boundary
    stripped = text.strip()
    if stripped and stripped[-1] in ".!?":
        d7 += 2.0
    # Length scoring (no penalty for long hooks — lecture hooks can be 60+ words)
    if 8 <= word_count <= 20:
        d7 += 1.5
    elif 20 < word_count <= 60:
        d7 += 1.0  # longer hooks are fine if narrative arc is complete
    elif word_count > 60:
        d7 += 0.5  # very long — still valid for lectures
    # Penalties
    if word_count < 5:
        d7 -= 1.0
    if not stripped or stripped[-1] not in ".!?\"'":
        d7 -= 1.0  # ends mid-clause
    scores.thought_completeness = max(0.0, min(10.0, d7))

    return scores


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPORAL POSITION MULTIPLIER
# ═══════════════════════════════════════════════════════════════════════════════

def _temporal_multiplier(start_seconds: float, narrative_score: float = 0.0) -> float:
    """Positional preference — soft, not a hard cutoff.

    Key insight: hook length depends on niche. A lecture hook can be 60s.
    So we DON'T heavily penalize later segments. Instead:
    - Early segments get a small boost (viewers decide to stay in first 3s)
    - Mid segments (3-60s) are treated nearly equally
    - Late segments (60s+) get a small reduction
    - High narrative_score compensates for later position
      (a complete tension arc at 45s is still a great hook)
    """
    # Base positional multiplier (much flatter than v3)
    if start_seconds <= 3:
        base = 1.20
    elif start_seconds <= 10:
        base = 1.15
    elif start_seconds <= 30:
        base = 1.10
    elif start_seconds <= 60:
        base = 1.05
    elif start_seconds <= 120:
        base = 0.95
    else:
        base = 0.85

    # Narrative completeness compensates for position:
    # A segment at 45s with full narrative arc (score 3-4) should score
    # almost as well as a segment at 3s with partial arc
    if narrative_score >= 3.0:
        base = max(base, 1.10)  # floor at 1.10 for complete arcs
    elif narrative_score >= 2.0:
        base = max(base, 1.00)  # floor at 1.00 for partial arcs

    return base


# ═══════════════════════════════════════════════════════════════════════════════
# TRIPLE COMBO BONUS
# ═══════════════════════════════════════════════════════════════════════════════

def _triple_combo_bonus(scroll_stop: float, curiosity_gap: float, emotional_voltage: float) -> float:
    """The highest-performing hooks combine: pattern interrupt + curiosity gap + viewer relevance."""
    has_interrupt = scroll_stop >= 6.0
    has_curiosity = curiosity_gap >= 5.0
    has_relevance = emotional_voltage >= 5.0

    combo = sum([has_interrupt, has_curiosity, has_relevance])
    if combo == 3:
        return 1.8
    if combo == 2:
        return 0.6
    return 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# FINAL SCORE COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

# Expert-aligned weights (sum = 1.0 for the 7 display dimensions)
DIMENSION_WEIGHTS = {
    "scroll_stop": 0.20,       # pattern_interrupt
    "curiosity_gap": 0.20,     # curiosity_gap
    "stakes_intensity": 0.10,  # part of emotional_trigger
    "emotional_voltage": 0.15, # direct_viewer_relevance
    "standalone_clarity": 0.10,
    "thematic_focus": 0.05,
    "thought_completeness": 0.10,
}
# Additional expert features scored separately (not in 7 display dims)
CONTRARIAN_WEIGHT = 0.10
NUMERICAL_WEIGHT = 0.10
AUTHORITY_WEIGHT = 0.10

MAX_THEORETICAL = 10.0 * 1.20 + 1.8 + 3.75 + 1.5 + 1.0  # ~20 (temporal + combo + grammar + tension + narrative)


def _compute_final_score(
    scores: _DimensionScores, start_seconds: float, text: str,
    authority_score: float,
) -> float:
    """Compute weighted final score with narrative-aware temporal adjustment,
    combo bonus, and template matching."""
    # 7-dimension weighted base
    weighted = (
        scores.scroll_stop * DIMENSION_WEIGHTS["scroll_stop"]
        + scores.curiosity_gap * DIMENSION_WEIGHTS["curiosity_gap"]
        + scores.stakes_intensity * DIMENSION_WEIGHTS["stakes_intensity"]
        + scores.emotional_voltage * DIMENSION_WEIGHTS["emotional_voltage"]
        + scores.standalone_clarity * DIMENSION_WEIGHTS["standalone_clarity"]
        + scores.thematic_focus * DIMENSION_WEIGHTS["thematic_focus"]
        + scores.thought_completeness * DIMENSION_WEIGHTS["thought_completeness"]
    )

    # Expert feature: contrarian signal (0-10 scale, weighted)
    contrarian = min(_match_score(text, CONTRAST_PATTERNS) + _match_score(text, NEGATION_PATTERNS), 10.0)
    weighted += contrarian * CONTRARIAN_WEIGHT

    # Expert feature: numerical specificity (0-10 scale, weighted)
    num_score = min(_match_score(text, NUMERICAL_PATTERNS), 5.0)
    if _NUM_RE.search(text):
        num_score += 3.0
    num_score = min(num_score, 10.0)
    weighted += num_score * NUMERICAL_WEIGHT

    # Expert feature: authority signal (0-10 scale, weighted)
    auth = min(authority_score, 10.0)
    weighted += auth * AUTHORITY_WEIGHT

    # Conceptual tension bonus (lecture/explainer hooks)
    tension = _match_score(text, CONCEPTUAL_TENSION_PATTERNS)
    misconception = _match_score(text, MISCONCEPTION_PATTERNS)
    if tension > 0 or misconception > 0:
        weighted += min((tension + misconception) * 0.15, 1.5)

    # Narrative-aware temporal multiplier
    narrative = _narrative_completion_score(text)
    temporal = _temporal_multiplier(start_seconds, narrative)
    combo = _triple_combo_bonus(scores.scroll_stop, scores.curiosity_gap, scores.emotional_voltage)
    template = _template_bonus(text)
    grammar = _grammar_bonus(text)

    raw = weighted * temporal + combo + max(template, grammar)  # best of template vs grammar

    # Narrative arc bonus: segments with a complete arc get extra credit
    if narrative >= 3.0:
        raw += 1.0
    elif narrative >= 2.0:
        raw += 0.4

    # Sentence length bonus: short punchy sentences (≤8 words) get a bump
    word_count = len(text.split())
    if word_count <= 8 and word_count >= 3:
        raw += 0.5

    # Normalize to 0-10
    return max(0.0, min(10.0, raw * (10.0 / MAX_THEORETICAL)))


# ═══════════════════════════════════════════════════════════════════════════════
# INSIGHT GENERATION (context-aware)
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_insights(text: str, hook_type: str, scores: _DimensionScores) -> tuple[str, str, str]:
    """Generate context-aware insights based on the specific hook content and scores."""

    # Identify the strongest and weakest dimensions
    dims = {
        "scroll_stop": scores.scroll_stop,
        "curiosity_gap": scores.curiosity_gap,
        "stakes_intensity": scores.stakes_intensity,
        "emotional_voltage": scores.emotional_voltage,
    }
    strongest = max(dims, key=dims.get)
    weakest = min(dims, key=dims.get)

    # Platform dynamics — based on hook type
    dynamics_map = {
        "Curiosity Gap": "Curiosity hooks drive 2-3x higher click-through. The unresolved information gap keeps viewers watching to close the loop, boosting average watch time.",
        "Pattern Interrupt": "Pattern interrupts reset the scroll reflex by violating expectations. This hook format has the highest first-second retention on Shorts.",
        "High Stakes Warning": "Warning-framed content triggers urgency sharing — viewers share risk content 40% more than opportunity content on short-form platforms.",
        "Fear-Based": "Loss aversion framing makes this hook 2x more compelling than equivalent gain framing. Fear hooks have the highest comment-to-view ratios.",
        "Authority": "Credibility signals in the first 3 seconds reduce skip rates by 25%. Authority hooks convert viewers to subscribers at 3x the rate of other types.",
        "Story-Based": "Narrative hooks increase average watch time by 65%. Story openings activate empathetic engagement that sustains attention through the full Short.",
        "Direct Benefit": "Clear benefit hooks drive the highest save/bookmark rates. Viewers who see immediate personal value stay 2x longer and share 3x more.",
        "Contrarian": "Contrarian takes generate 3x more comments through agreement and disagreement. This engagement signal boosts algorithmic distribution significantly.",
        "Counterintuitive": "Counterintuitive claims trigger cognitive dissonance, forcing viewers to watch the explanation. These hooks have the lowest early-exit rates.",
        "Personal Transformation": "Transformation hooks work because viewers project themselves into the before/after arc. They drive the highest 'watch again' rates.",
        "FOMO Setup": "Urgency framing bypasses rational evaluation. FOMO hooks drive immediate action — highest click-through rates of all hook types.",
        "Zero-Second Claim": "Bold claims in the first second capture attention before the viewer's thumb reaches the swipe zone. Critical for algorithmic first-impression scoring.",
        "Social Proof": "Numerical social proof ('10K people') creates bandwagon effect. Viewers trust content validated by crowd behavior.",
        "Pain Escalation": "Layered pain statements intensify viewer investment. Each pain point makes the eventual solution feel more valuable.",
    }

    # Viewer psychology — based on strongest dimension
    psychology_map = {
        "scroll_stop": "This hook exploits the orienting response — an involuntary neurological reflex triggered by unexpected stimuli that forces the brain to pause and evaluate.",
        "curiosity_gap": "The Zeigarnik effect creates psychological tension from incomplete information. Viewers feel compelled to continue watching to resolve the open question.",
        "stakes_intensity": "Loss aversion makes threats feel 2x more intense than equivalent opportunities. The viewer's brain prioritizes processing this perceived risk.",
        "emotional_voltage": "Direct viewer address activates the self-referencing effect — content framed as personally relevant gets encoded in memory more deeply.",
    }

    # Improvement suggestion — based on weakest dimension
    tip_map = {
        "scroll_stop": f"Strengthen the opening impact: start with a shorter, punchier first sentence (aim for 3-5 words). Current hook could benefit from a stronger pattern interrupt.",
        "curiosity_gap": f"Add an open loop: hint at specific information without revealing it. 'There's one thing that...' or 'The part nobody mentions is...' would increase tension.",
        "stakes_intensity": f"Quantify the stakes: replace vague risk/reward with specific numbers. '$50K mistake' hits harder than 'big mistake'. Add a concrete metric.",
        "emotional_voltage": f"Increase personal relevance: add direct 'you' address or identity targeting ('If you're a creator...'). Make the viewer feel this is specifically about them.",
    }

    dynamics = dynamics_map.get(hook_type, f"This {hook_type} hook shows strong engagement potential with a {strongest.replace('_', ' ')} score of {dims[strongest]:.1f}/10.")
    psychology = psychology_map.get(strongest, "This content triggers multiple engagement drivers simultaneously, creating layered viewer investment.")
    tip = tip_map.get(weakest, "Focus on making the opening line self-contained and immediately compelling without requiring any context.")

    return dynamics, psychology, tip


# ═══════════════════════════════════════════════════════════════════════════════
# ATTENTION SIGNAL HIERARCHY (5-tier weighted detection)
# ═══════════════════════════════════════════════════════════════════════════════
# Tier 1 (3.0): Cognitive Shock — prediction error, belief violation
# Tier 2 (2.5): Curiosity Gap — information asymmetry
# Tier 3 (2.0): Stakes & Consequences — risk/reward
# Tier 4 (1.5): Viewer Relevance — direct address
# Tier 5 (1.0): Structural Narrative — organization signals

def _tiered_signal_score(text: str) -> float:
    """Compute attention score using 5-tier signal hierarchy."""
    score = 0.0
    text_lower = text.lower()

    # Tier 1 (3.0): Cognitive shock — contradictions, belief violations
    t1 = 0
    if _match_count(text, CONTRAST_PATTERNS) > 0:
        t1 += 1
    if _match_count(text, NEGATION_PATTERNS) > 0:
        t1 += 1
    if _match_count(text, MISCONCEPTION_PATTERNS) > 0:
        t1 += 1
    if _match_count(text, CONCEPTUAL_TENSION_PATTERNS) > 0:
        t1 += 1
    score += min(t1, 3) * 3.0

    # Tier 2 (2.5): Curiosity gap
    t2 = 0
    if _match_count(text, OPEN_LOOP_PATTERNS) > 0:
        t2 += 1
    if _match_count(text, MYSTERY_PATTERNS) > 0:
        t2 += 1
    score += min(t2, 2) * 2.5

    # Tier 3 (2.0): Stakes
    t3 = 0
    if _match_count(text, RISK_PATTERNS) > 0:
        t3 += 1
    if _match_count(text, REWARD_PATTERNS) > 0:
        t3 += 1
    score += min(t3, 2) * 2.0

    # Tier 4 (1.5): Viewer relevance
    you_count = len(_YOU_RE.findall(text))
    if you_count > 0:
        score += 1.5
    if _match_count(text, IDENTITY_PATTERNS) > 0:
        score += 1.5

    # Tier 5 (1.0): Structural narrative
    if _match_count(text, EXPLANATION_PATTERNS) > 0:
        score += 1.0

    return score


# ═══════════════════════════════════════════════════════════════════════════════
# HOOK DENSITY MAP (sliding window attention density)
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_density_map(
    segments: list[dict], window_sec: float = 8.0, step_sec: float = 3.0,
) -> list[dict]:
    """Compute attention signal density across the transcript timeline.

    Returns list of {start, end, density, texts} for each window.
    Density peaks indicate hook candidate clusters.
    """
    if not segments:
        return []

    max_time = max(s.get("end", s["start"] + 15) for s in segments)
    windows: list[dict] = []
    t = 0.0

    while t < max_time:
        win_end = t + window_sec
        # Collect segments that overlap this window
        win_texts: list[str] = []
        for seg in segments:
            seg_start = seg["start"]
            seg_end = seg.get("end", seg_start + 15)
            if seg_start < win_end and seg_end > t:
                win_texts.append(seg["text"])

        if win_texts:
            combined = " ".join(win_texts)
            density = _tiered_signal_score(combined)
            windows.append({
                "start": t,
                "end": win_end,
                "density": density,
                "text": combined,
            })

        t += step_sec

    return windows


def _find_density_peaks(
    density_map: list[dict], threshold: float = 6.0,
) -> list[dict]:
    """Find windows where density exceeds threshold (hook candidate regions)."""
    peaks: list[dict] = []
    for win in density_map:
        if win["density"] >= threshold:
            # Merge with previous peak if adjacent
            if peaks and win["start"] <= peaks[-1]["end"]:
                peaks[-1]["end"] = win["end"]
                peaks[-1]["density"] = max(peaks[-1]["density"], win["density"])
                peaks[-1]["text"] += " " + win["text"]
            else:
                peaks.append(dict(win))
    return peaks


# ═══════════════════════════════════════════════════════════════════════════════
# HOOK STATE MACHINE (sequential narrative state tracking)
# ═══════════════════════════════════════════════════════════════════════════════
# Tracks: NEUTRAL → OBSERVATION → EXPECTATION → CONTRADICTION →
#         ESCALATION → CURIOSITY_PEAK → EXPLANATION
# Extracts hooks from OBSERVATION start → CURIOSITY_PEAK end.

_SM_NEUTRAL = 0
_SM_OBSERVATION = 1
_SM_EXPECTATION = 2
_SM_CONTRADICTION = 3
_SM_ESCALATION = 4
_SM_CURIOSITY_PEAK = 5
_SM_EXPLANATION = 6


def _detect_state_signals(text: str) -> dict[str, bool]:
    """Detect which narrative state signals are present in a sentence."""
    text_lower = text.lower()
    return {
        "observation": (
            _match_count(text, CONCEPTUAL_TENSION_PATTERNS) > 0
            or any(w in text_lower for w in [
                "strange", "weird", "interesting", "surprising",
                "unexpected", "remarkable", "fascinating",
            ])
            or _match_count(text, IMPERATIVE_PATTERNS) > 0
            or _match_count(text, RISK_PATTERNS) > 0
        ),
        "expectation": any(p in text_lower for p in [
            "most people", "you might expect", "you would expect",
            "it seems", "we usually", "you probably think",
            "we tend to", "in school", "commonly", "the way we imagine",
            "picture a", "imagine a", "you might assume",
        ]),
        "contradiction": any(p in text_lower for p in [
            "but that's not", "but actually", "but it turns out",
            "however", "that's not true", "that's not how",
            "completely wrong", "actually wrong", "not actually",
            "but the truth", "but in reality", "but that's actually",
        ]),
        "escalation": any(p in text_lower for p in [
            "in fact", "even stranger", "the real mystery",
            "even more", "what's really", "it gets worse",
            "it gets stranger", "not only that", "and it gets",
            "the deeper", "even worse",
        ]),
        "curiosity_peak": (
            "?" in text
            or any(p in text_lower for p in [
                "so how", "so why", "so what happens",
                "to understand", "the answer lies",
                "here's what's actually", "the real reason",
            ])
        ),
        "explanation": _match_count(text, EXPLANATION_PATTERNS) > 0,
        "filler": _match_count(text, FILLER_PATTERNS) >= 2,
    }


@dataclass
class _StateMachineHook:
    """A hook arc detected by the state machine."""
    start_seconds: float
    end_seconds: float
    text: str
    max_state: int  # highest state reached (0-6)
    stages_hit: int  # number of distinct stages traversed


def _run_state_machine(segments: list[dict]) -> list[_StateMachineHook]:
    """Run the hook state machine over sequential transcript segments.

    Returns detected hook arcs (may find multiple in long transcripts).
    """
    # Sort by start time
    sorted_segs = sorted(segments, key=lambda s: s["start"])
    # Deduplicate: only use single-sentence segments (not windows)
    seen_starts: set[float] = set()
    unique_segs: list[dict] = []
    for seg in sorted_segs:
        if seg["start"] not in seen_starts:
            seen_starts.add(seg["start"])
            unique_segs.append(seg)

    hooks: list[_StateMachineHook] = []
    state = _SM_NEUTRAL
    hook_start = 0.0
    hook_text_parts: list[str] = []
    stages_hit = 0
    max_state = 0

    for seg in unique_segs:
        text = _normalize_transcript(seg["text"].strip())
        if not text:
            continue

        signals = _detect_state_signals(text)

        # Skip filler
        if signals["filler"]:
            continue

        if state == _SM_NEUTRAL:
            if signals["observation"]:
                state = _SM_OBSERVATION
                hook_start = seg["start"]
                hook_text_parts = [text]
                stages_hit = 1
                max_state = _SM_OBSERVATION

        elif state == _SM_OBSERVATION:
            hook_text_parts.append(text)
            if signals["expectation"]:
                state = _SM_EXPECTATION
                stages_hit += 1
                max_state = _SM_EXPECTATION
            elif signals["contradiction"]:
                # Skip expectation, go straight to contradiction
                state = _SM_CONTRADICTION
                stages_hit += 1
                max_state = _SM_CONTRADICTION

        elif state == _SM_EXPECTATION:
            hook_text_parts.append(text)
            if signals["contradiction"]:
                state = _SM_CONTRADICTION
                stages_hit += 1
                max_state = _SM_CONTRADICTION

        elif state == _SM_CONTRADICTION:
            hook_text_parts.append(text)
            if signals["escalation"]:
                state = _SM_ESCALATION
                stages_hit += 1
                max_state = _SM_ESCALATION
            elif signals["curiosity_peak"]:
                state = _SM_CURIOSITY_PEAK
                stages_hit += 1
                max_state = _SM_CURIOSITY_PEAK

        elif state == _SM_ESCALATION:
            hook_text_parts.append(text)
            if signals["curiosity_peak"]:
                state = _SM_CURIOSITY_PEAK
                stages_hit += 1
                max_state = _SM_CURIOSITY_PEAK

        elif state == _SM_CURIOSITY_PEAK:
            # Hook is complete — check for explanation start
            if signals["explanation"]:
                state = _SM_EXPLANATION

        # Emit hook when we reach curiosity peak or explanation
        if state in (_SM_CURIOSITY_PEAK, _SM_EXPLANATION) and stages_hit >= 2:
            hook_end = seg.get("end", seg["start"] + 15)
            hooks.append(_StateMachineHook(
                start_seconds=hook_start,
                end_seconds=hook_end,
                text=" ".join(hook_text_parts),
                max_state=max_state,
                stages_hit=stages_hit,
            ))
            # Reset for potential next hook
            state = _SM_NEUTRAL
            hook_text_parts = []
            stages_hit = 0
            max_state = 0

        # Timeout: if we've been building for too long without progression, reset
        if state > _SM_NEUTRAL and seg["start"] - hook_start > 120:
            # Save partial hook if it reached contradiction
            if max_state >= _SM_CONTRADICTION and stages_hit >= 2:
                hooks.append(_StateMachineHook(
                    start_seconds=hook_start,
                    end_seconds=seg.get("end", seg["start"] + 15),
                    text=" ".join(hook_text_parts),
                    max_state=max_state,
                    stages_hit=stages_hit,
                ))
            state = _SM_NEUTRAL
            hook_text_parts = []
            stages_hit = 0
            max_state = 0

    # Flush any in-progress hook that reached at least contradiction
    if max_state >= _SM_CONTRADICTION and stages_hit >= 2:
        last_seg = unique_segs[-1] if unique_segs else {"start": 0, "end": 15}
        hooks.append(_StateMachineHook(
            start_seconds=hook_start,
            end_seconds=last_seg.get("end", last_seg["start"] + 15),
            text=" ".join(hook_text_parts),
            max_state=max_state,
            stages_hit=stages_hit,
        ))

    return hooks


# ═══════════════════════════════════════════════════════════════════════════════
# SCORED SEGMENT DATACLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class _ScoredSegment:
    text: str
    start_seconds: float
    end_seconds: float
    final_score: float
    dimensions: _DimensionScores
    hook_type: str
    funnel_role: str


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _seconds_to_timestamp(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


class DeterministicEngine:
    """
    Deterministic hook identification v4 — no LLM calls.

    Three-layer detection pipeline:

    Layer 1 — Hook State Machine: sequential narrative state tracking
      NEUTRAL → OBSERVATION → EXPECTATION → CONTRADICTION →
      ESCALATION → CURIOSITY_PEAK → EXPLANATION
      Detects complete narrative arcs (works especially well for educational content).

    Layer 2 — Hook Density Map: sliding window attention signal density
      5-tier signal hierarchy (cognitive shock 3.0 → structural 1.0)
      Finds attention clusters across the full timeline, not just the start.

    Layer 3 — Per-segment scoring: 7 dimensions + 3 expert features +
      15 viral templates + narrative phase detection + temporal multiplier

    Cross-layer integration: segments get bonuses when confirmed by
    state machine arcs and/or density peaks. State machine arcs are also
    scored as standalone candidates.

    Key principle: Hook length = narrative tension arc, NOT fixed duration.
    Short-form hooks (3-10s) and lecture hooks (30-90s) are both valid.
    """

    def analyze(
        self, transcript: str, niche: str, language: str = "English",
        rules: list[dict] | None = None,
    ) -> HookEngineResult:
        logger.info("Running deterministic hook analysis v4 (no LLM)")

        segments = _parse_transcript_segments(transcript)
        if not segments:
            from app.exceptions import HookEngineError
            raise HookEngineError("Could not parse transcript into segments")

        # Get niche preferences
        niche_config = NICHES.get(niche, NICHES.get("Generic", {}))
        preferred_types = niche_config.get("preferredTypes", [])

        # ── Layer 1: State machine — detect narrative arcs ──
        sm_hooks = _run_state_machine(segments)
        logger.info("State machine found %d narrative arcs", len(sm_hooks))

        # ── Layer 2: Density map — find attention clusters ──
        density_map = _compute_density_map(segments)
        density_peaks = _find_density_peaks(density_map, threshold=6.0)
        logger.info("Density map found %d attention peaks", len(density_peaks))

        # ── Layer 3: Per-segment scoring ──
        scored: list[_ScoredSegment] = []
        for seg in segments:
            text = _normalize_transcript(seg["text"].strip())
            if not text or len(text.split()) < 4:
                continue

            # Reject filler
            filler_hits = _match_count(text, FILLER_PATTERNS)
            if filler_hits >= 2:
                continue

            # Trim at hook boundary if detected
            boundary = _detect_hook_end(text)
            if boundary and boundary > 30:
                text = text[:boundary].rstrip()

            # Score all 7 dimensions
            dims = _score_dimensions(text)

            # Compute auxiliary scores for classification
            authority_s = _match_score(text, AUTHORITY_PATTERNS)
            story_s = _match_score(text, STORY_PATTERNS)
            benefit_s = _match_score(text, BENEFIT_PATTERNS)

            # Classify hook type
            hook_type, funnel_role = _classify_hook_type(
                dims.scroll_stop, dims.curiosity_gap, dims.stakes_intensity,
                dims.emotional_voltage, text, authority_s, story_s, benefit_s,
            )

            # Niche bonus: boost score if hook type is preferred for this niche
            niche_bonus = 0.0
            if hook_type in preferred_types:
                niche_bonus = 0.8

            # Compute final score
            final = _compute_final_score(dims, seg["start"], text, authority_s) + niche_bonus

            # ── Cross-layer bonuses ──
            seg_start = seg["start"]
            seg_end = seg.get("end", seg_start + 15)

            # Bonus if segment falls within a state machine hook arc
            for sm in sm_hooks:
                if seg_start >= sm.start_seconds and seg_end <= sm.end_seconds + 5:
                    # Scale bonus by how many stages the arc traversed
                    sm_bonus = 0.3 * sm.stages_hit
                    final += min(sm_bonus, 1.5)
                    break

            # Bonus if segment falls within a density peak
            for peak in density_peaks:
                if seg_start < peak["end"] and seg_end > peak["start"]:
                    # Density > 6 means multiple strong signals clustered here
                    density_bonus = min((peak["density"] - 6.0) * 0.15, 1.0)
                    final += density_bonus
                    break

            final = min(10.0, final)

            # Skip very weak segments
            if final < 1.5:
                continue

            scored.append(_ScoredSegment(
                text=text,
                start_seconds=seg_start,
                end_seconds=seg_end,
                final_score=final,
                dimensions=dims,
                hook_type=hook_type,
                funnel_role=funnel_role,
            ))

        # ── Also score state machine arcs as candidates ──
        for sm in sm_hooks:
            if sm.stages_hit < 3:
                continue  # Only use arcs with substantial progression
            text = sm.text
            if len(text.split()) < 6:
                continue

            # Trim at hook boundary
            boundary = _detect_hook_end(text)
            if boundary and boundary > 30:
                text = text[:boundary].rstrip()

            dims = _score_dimensions(text)
            authority_s = _match_score(text, AUTHORITY_PATTERNS)
            story_s = _match_score(text, STORY_PATTERNS)
            benefit_s = _match_score(text, BENEFIT_PATTERNS)
            hook_type, funnel_role = _classify_hook_type(
                dims.scroll_stop, dims.curiosity_gap, dims.stakes_intensity,
                dims.emotional_voltage, text, authority_s, story_s, benefit_s,
            )
            niche_bonus = 0.8 if hook_type in preferred_types else 0.0
            final = _compute_final_score(dims, sm.start_seconds, text, authority_s) + niche_bonus
            # State machine arc bonus (complete arcs are high confidence)
            final += 0.3 * sm.stages_hit
            final = min(10.0, final)

            if final >= 2.0:
                scored.append(_ScoredSegment(
                    text=text[:500],  # cap very long arcs
                    start_seconds=sm.start_seconds,
                    end_seconds=sm.end_seconds,
                    final_score=final,
                    dimensions=dims,
                    hook_type=hook_type,
                    funnel_role=funnel_role,
                ))

        # Sort by score descending
        scored.sort(key=lambda s: s.final_score, reverse=True)

        if not scored:
            from app.exceptions import HookEngineError
            raise HookEngineError("No hook candidates found in transcript")

        # Select top 5 non-overlapping, type-diverse hooks
        selected = self._select_top_5(scored, preferred_types)

        # Re-rank by final score
        selected.sort(key=lambda s: s.final_score, reverse=True)

        # Build HookCandidates
        hooks: list[HookCandidate] = []
        for rank, seg in enumerate(selected, 1):
            d = seg.dimensions
            score_dict = {
                "scroll_stop": round(d.scroll_stop, 1),
                "curiosity_gap": round(d.curiosity_gap, 1),
                "stakes_intensity": round(d.stakes_intensity, 1),
                "emotional_voltage": round(d.emotional_voltage, 1),
                "standalone_clarity": round(d.standalone_clarity, 1),
                "thematic_focus": round(d.thematic_focus, 1),
                "thought_completeness": round(d.thought_completeness, 1),
            }

            # Attention score = final score (already incorporates all weights)
            attention = round(seg.final_score, 1)

            # Truncate display text
            hook_text = seg.text
            if len(hook_text) > 250:
                hook_text = hook_text[:247] + "..."

            dynamics, psychology, tip = _generate_insights(seg.text, seg.hook_type, seg.dimensions)

            hooks.append(HookCandidate(
                rank=rank,
                hook_text=hook_text,
                start_time=_seconds_to_timestamp(seg.start_seconds),
                end_time=_seconds_to_timestamp(seg.end_seconds),
                start_seconds=seg.start_seconds,
                end_seconds=seg.end_seconds,
                hook_type=seg.hook_type,
                funnel_role=seg.funnel_role,
                scores=score_dict,
                attention_score=attention,
                platform_dynamics=dynamics,
                viewer_psychology=psychology,
                improvement_suggestion=tip,
                is_composite=False,
            ))

        return HookEngineResult(
            hooks=hooks,
            provider="deterministic",
            model="rule-based-v4",
            attempts=1,
            input_tokens=None,
            output_tokens=None,
        )

    def _select_top_5(
        self, candidates: list[_ScoredSegment], preferred_types: list[str],
    ) -> list[_ScoredSegment]:
        """Select top 5 non-overlapping hooks with type diversity."""
        selected: list[_ScoredSegment] = []
        types_used: set[str] = set()

        # Pass 1: Greedily pick top non-overlapping candidates
        for c in candidates:
            if len(selected) >= 5:
                break
            if not any(self._overlaps(c, s) for s in selected):
                selected.append(c)
                types_used.add(c.hook_type)

        # Pass 2: If fewer than 3 unique types, swap weakest duplicate with a new type
        if len(types_used) < 3 and len(selected) >= 3:
            for c in candidates:
                if c.hook_type in types_used or c in selected:
                    continue
                if any(self._overlaps(c, s) for s in selected):
                    continue

                # Find weakest duplicate-type segment to replace
                type_counts: dict[str, int] = {}
                for s in selected:
                    type_counts[s.hook_type] = type_counts.get(s.hook_type, 0) + 1
                duplicates = [s for s in selected if type_counts.get(s.hook_type, 0) > 1]
                if duplicates:
                    weakest = min(duplicates, key=lambda s: s.final_score)
                    selected.remove(weakest)
                    selected.append(c)
                    types_used.add(c.hook_type)

                if len(types_used) >= 3:
                    break

        # Pass 3: Fill remaining slots if we have fewer than 5
        if len(selected) < 5:
            for c in candidates:
                if len(selected) >= 5:
                    break
                if c not in selected and not any(self._overlaps(c, s) for s in selected):
                    selected.append(c)

        return selected[:5]

    @staticmethod
    def _overlaps(a: _ScoredSegment, b: _ScoredSegment) -> bool:
        """Check if two segments overlap in time."""
        return a.start_seconds < b.end_seconds and b.start_seconds < a.end_seconds
