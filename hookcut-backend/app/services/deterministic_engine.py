"""
Deterministic hook identification engine v5 (simplified) — no LLM calls.

Core principle: Hooks must convey complete thoughts. They should never
start or end mid-sentence. The engine groups transcript segments into
sentence-complete chunks, scores them on basic engagement signals, and
selects the top 5 non-overlapping hooks.

Admin-only: controlled by HOOK_ENGINE_MODE setting (stored in Redis).
"""

import re
import logging
from dataclasses import dataclass

from app.services.hook_engine import HookCandidate, HookEngineResult
from app.llm.prompts.constants import NICHES

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# WORD-BOUNDARY KEYWORD MATCHING
# ═══════════════════════════════════════════════════════════════════════════════

def _compile_patterns(keywords: dict[str, float]) -> list[tuple[re.Pattern, float]]:
    """Compile keyword dict into (regex, weight) pairs with word boundaries."""
    patterns = []
    for kw, weight in keywords.items():
        if " " in kw:
            patterns.append((re.compile(re.escape(kw), re.IGNORECASE), weight))
        else:
            patterns.append((re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE), weight))
    return patterns


def _match_score(text: str, patterns: list[tuple[re.Pattern, float]]) -> float:
    """Sum weighted matches for a text against compiled patterns."""
    return sum(weight for pat, weight in patterns if pat.search(text))


def _match_count(text: str, patterns: list[tuple[re.Pattern, float]]) -> int:
    """Count how many patterns match (unweighted)."""
    return sum(1 for pat, _ in patterns if pat.search(text))


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL KEYWORD DICTIONARIES
# ═══════════════════════════════════════════════════════════════════════════════

# Attention-grabbing signals (pattern interrupts, contrarian claims)
ATTENTION_PATTERNS = _compile_patterns({
    "stop": 1.5, "wait": 1.5, "listen": 1.5, "hold on": 2.0, "hold up": 2.0,
    "don't": 1.0, "never": 1.0, "forget everything": 3.0, "pay attention": 2.0,
    "everyone thinks": 2.5, "most people think": 2.5, "you think": 2.0,
    "but actually": 2.5, "but the truth is": 3.0, "but here's the thing": 3.0,
    "you're doing this wrong": 3.0, "not what you think": 2.5,
    "you've been lied to": 3.0, "this is wrong": 2.0,
})

# Curiosity gap signals
CURIOSITY_PATTERNS = _compile_patterns({
    "this is why": 2.5, "nobody tells you": 3.0, "here's the thing": 3.0,
    "here's the trick": 3.0, "here's what": 2.5, "here's why": 2.5,
    "nobody talks about": 3.0, "what nobody mentions": 3.0,
    "the truth about": 2.5, "the real reason": 2.5, "the truth is": 2.5,
    "ever wonder": 2.0, "did you know": 2.0, "you won't believe": 2.5,
    "secret": 2.0, "hidden": 2.0, "little-known": 2.5, "little known": 2.5,
})

# Stakes signals (risk + reward)
STAKES_PATTERNS = _compile_patterns({
    "mistake": 2.0, "danger": 2.0, "dangerous": 2.0, "ruin": 2.5,
    "lose": 1.5, "fail": 1.5, "destroy": 2.5, "waste": 1.5,
    "risk": 1.5, "warning": 2.0, "biggest mistake": 3.0,
    "hack": 1.5, "growth": 1.5, "money": 1.5, "revenue": 1.5,
    "unlock": 2.0, "million": 2.0, "breakthrough": 2.5,
    "changed my life": 3.0, "game changer": 2.5, "cheat code": 2.5,
})

# Authority signals
AUTHORITY_PATTERNS = _compile_patterns({
    "research shows": 2.5, "studies show": 2.5, "according to": 2.0,
    "scientifically proven": 3.0, "after 10 years": 3.0,
    "years of experience": 2.5, "data shows": 2.0, "expert": 1.5,
})

# Story signals
STORY_PATTERNS = _compile_patterns({
    "i was": 1.0, "i used to": 1.5, "when i": 1.0, "years ago": 1.5,
    "one day": 1.5, "true story": 2.5, "i'll never forget": 3.0,
    "that's when i realized": 3.0, "let me tell you": 2.0,
})

# Benefit signals
BENEFIT_PATTERNS = _compile_patterns({
    "step by step": 2.5, "how to": 2.0, "in just": 2.0,
    "the only way": 2.5, "exact method": 2.5, "simple trick": 2.0,
    "method": 1.0, "technique": 1.0, "template": 1.5,
})

# Identity / viewer relevance
IDENTITY_PATTERNS = _compile_patterns({
    "if you're a": 3.0, "if you're doing this": 3.0,
    "if you want": 2.0, "if you're struggling": 3.0,
    "if you're trying": 2.5, "as a creator": 2.5,
    "as a founder": 2.5, "as a developer": 2.5,
})

# Filler / sponsor signals (for rejection)
FILLER_PATTERNS = _compile_patterns({
    "subscribe": 1.0, "like button": 1.0, "hit the bell": 1.0,
    "comment below": 1.0, "share this": 1.0, "follow me": 1.0,
    "link in description": 1.0, "link in the description": 1.0,
    "sponsor": 1.0, "brought to you by": 1.0,
    "hello everyone": 1.0, "hey guys": 1.0, "what's up": 1.0,
    "welcome back": 1.0, "thanks for watching": 1.0,
    "see you next": 1.0, "make sure to": 1.0,
    "don't forget to subscribe": 1.0, "smash that": 1.0,
    "this video is sponsored": 1.0, "today's sponsor": 1.0,
    "use code": 1.0, "use my link": 1.0, "promo code": 1.0,
    "drop a comment": 1.0, "leave a comment": 1.0,
    "links in the description": 1.0, "link is in the description": 1.0,
    "i made a full video": 1.0, "check out my": 1.0,
    "whatsapp community": 1.0, "join my": 1.0,
    "let me know in the comments": 1.0, "what would you": 1.0,
    "let's get there together": 1.0, "that's the game": 1.0,
    "if you enjoyed": 1.0, "if you liked": 1.0,
    "go watch": 1.0, "go check out": 1.0,
    "pairs perfectly with": 1.0, "i'll help you": 1.0,
    "want to take this further": 1.0, "take this even further": 1.0,
    "i'll see you": 1.0, "see you in the next": 1.0,
    "peace": 1.0, "bye": 1.0,
})

# Regex helpers
_NUM_RE = re.compile(r'\b\d+%|\b\d+[xX]\b|\$[\d,]+[kKmMbB]?|\b\d+[kKmMbB]\b')
_YOU_RE = re.compile(r"\byou(?:'re|r|rself)?\b", re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSCRIPT PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_transcript(text: str) -> str:
    """Clean transcript text of artifacts."""
    text = re.sub(r'\[(?:Music|Applause|Laughter)\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _parse_timestamp(ts_str: str) -> float | None:
    """Parse a timestamp string like '0:00.08' or '1:23' into seconds."""
    # Handle M:SS.cc format — keep decimal precision
    decimal = 0.0
    if "." in ts_str:
        main, frac = ts_str.split(".", 1)
        decimal = float("0." + frac)
        ts_str = main

    parts = ts_str.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1]) + decimal
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]) + decimal
    return None


def _parse_transcript_segments(transcript: str) -> list[dict]:
    """Parse timestamped transcript into [{start, end, text}, ...].

    Supports formats:
      [M:SS.cc] text     (youtube_transcript_api)
      M:SS text          (plain)
    """
    pattern = re.compile(
        r'(?:\[)?(\d{1,2}:\d{2}(?:\.\d+)?(?::\d{2})?)\]?\s*'
        r'(.*?)(?=(?:\[)?\d{1,2}:\d{2}|\Z)',
        re.DOTALL,
    )

    matches = list(pattern.finditer(transcript))
    if not matches:
        return []

    segments: list[dict] = []
    for i, m in enumerate(matches):
        ts_str = m.group(1)
        text = _normalize_transcript(m.group(2))
        if not text:
            continue

        start = _parse_timestamp(ts_str)
        if start is None:
            continue

        # End time = next segment's start or start + 15
        end = start + 15.0
        if i + 1 < len(matches):
            next_start = _parse_timestamp(matches[i + 1].group(1))
            if next_start is not None:
                end = next_start

        segments.append({"start": float(start), "end": float(end), "text": text})

    # Ensure minimum segment duration
    for seg in segments:
        if seg["end"] - seg["start"] < 5:
            seg["end"] = seg["start"] + 15.0

    return segments


# ═══════════════════════════════════════════════════════════════════════════════
# SENTENCE RECONSTRUCTION & HOOK WINDOW GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def _ends_with_complete_sentence(text: str) -> bool:
    """Check if text ends with sentence-ending punctuation."""
    stripped = text.rstrip()
    return bool(stripped) and stripped[-1] in '.!?'


def _reconstruct_sentences(segments: list[dict]) -> list[dict]:
    """Reconstruct full sentences from transcript fragments.

    YouTube transcript segments are 2-4 second word fragments that often
    contain multiple sentence boundaries mid-fragment (e.g. "anything else.
    It's not prompting. It's"). This function:
    1. Joins all fragments into a continuous stream
    2. Splits at sentence boundaries (.!?)
    3. Interpolates timestamps based on word position
    """
    if not segments:
        return []

    # Build a word-level timeline: [(word, estimated_time), ...]
    # Use segment start times (reliable) and interpolate within each segment
    # Duration = gap to next segment's start (not the unreliable end time)
    word_times: list[tuple[str, float]] = []
    for i, seg in enumerate(segments):
        words = seg["text"].split()
        if not words:
            continue
        # Duration = time until next segment starts
        if i + 1 < len(segments):
            seg_duration = max(segments[i + 1]["start"] - seg["start"], 0.5)
        else:
            seg_duration = 3.0  # assume ~3s for last segment
        for j, w in enumerate(words):
            t = seg["start"] + (j / max(len(words), 1)) * seg_duration
            word_times.append((w, t))

    if not word_times:
        return []

    # Join all words and split into sentences
    full_text = " ".join(w for w, _ in word_times)

    # Split at sentence boundaries: period, exclamation, question mark
    # followed by a space and uppercase letter (or end of string)
    sentence_splits = re.split(r'(?<=[.!?])\s+(?=[A-Z])', full_text)

    # Map each sentence back to timestamps
    sentences: list[dict] = []
    word_idx = 0
    for sent_text in sentence_splits:
        sent_text = sent_text.strip()
        if not sent_text:
            continue

        sent_words = sent_text.split()
        if not sent_words:
            continue

        start_time = word_times[word_idx][1] if word_idx < len(word_times) else 0
        end_idx = min(word_idx + len(sent_words) - 1, len(word_times) - 1)
        end_time = word_times[end_idx][1] + 2.0  # add ~2s buffer for last word

        sentences.append({
            "start": start_time,
            "end": end_time,
            "text": _normalize_transcript(sent_text),
        })

        word_idx += len(sent_words)

    return sentences


def _is_standalone_opening(sentence_text: str) -> bool:
    """Check if a sentence works as a standalone hook opening.

    Rejects sentences that depend on prior context — continuation words,
    pronoun references to something not in the hook, list continuations, etc.
    A hook must make sense to someone who hasn't seen the prior content.
    """
    text = sentence_text.strip()
    if not text:
        return False

    # Continuation conjunctions — these signal the sentence follows from something
    _CONTINUATION_STARTS = re.compile(
        r'^(?:But|So|And|Or|Yet|However|Also|Plus|Instead|Meanwhile|Then|'
        r'Still|Maybe|Perhaps|Though|Although|Otherwise|Rather|'
        r'Similarly|Likewise|Furthermore|Moreover|Nevertheless|'
        r'Nonetheless|Consequently|Therefore|Hence|Thus|Besides|'
        r'Accordingly|Alternatively)\b',
        re.IGNORECASE,
    )
    if _CONTINUATION_STARTS.match(text):
        return False

    # Pronoun references to prior context ("It's", "That's", "This is", "These are")
    _DANGLING_PRONOUN_STARTS = re.compile(
        r"^(?:It'?s|It is|That'?s|That is|This is|These are|Those are|"
        r"They'?re|They are|There'?s|There is|Here'?s|Here is)\b",
        re.IGNORECASE,
    )
    # Exception: "Here's the thing/trick/why" patterns are strong openers
    _HERES_EXCEPTION = re.compile(
        r"^Here'?s (?:the thing|the trick|why|what|how|the real)",
        re.IGNORECASE,
    )
    if _DANGLING_PRONOUN_STARTS.match(text) and not _HERES_EXCEPTION.match(text):
        return False

    # List continuations ("Step two", "Number three", "Second,", "Third,")
    _LIST_CONTINUATION = re.compile(
        r'^(?:Step (?:two|three|four|five|six|seven|eight|nine|ten|\d+)|'
        r'Number (?:two|three|four|five|six|seven|eight|nine|ten|\d+)|'
        r'(?:Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)(?:ly|,))',
        re.IGNORECASE,
    )
    if _LIST_CONTINUATION.match(text):
        return False

    # Bare "Now" + verb continuation ("Now I", "Now you", "Now we", "Now let's")
    if re.match(r'^Now (?:I|you|we|let)', text, re.IGNORECASE):
        return False

    # "Which" relative clause continuations
    if text.startswith("Which "):
        return False

    return True


def _ends_with_complete_thought(text: str) -> bool:
    """Check if the text ends with a complete thought (not trailing off)."""
    stripped = text.rstrip()
    if not stripped:
        return False
    # Must end with sentence-ending punctuation
    if stripped[-1] not in '.!?':
        return False
    # Reject if ends with a setup word that expects continuation
    _TRAILING_SETUP = re.compile(
        r'(?:such as|like|including|especially|for example|for instance|'
        r'whether|because|since|although|while|when|where|which|that|'
        r'and|but|or|so)\s*[.!?]\s*$',
        re.IGNORECASE,
    )
    if _TRAILING_SETUP.search(stripped):
        return False
    return True


def _build_hook_windows(
    sentences: list[dict],
    min_sentences: int = 3,
    max_sentences: int = 5,
    min_duration: float = 10.0,
    max_duration: float = 30.0,
) -> list[dict]:
    """Build overlapping windows of consecutive sentences as hook candidates.

    Each window contains 2-5 complete sentences, ensuring hooks always
    start and end at sentence boundaries AND convey complete thoughts.
    Windows are rejected if they start with continuation markers or
    dangling references that require prior context.
    """
    windows: list[dict] = []

    for window_size in range(min_sentences, max_sentences + 1):
        for i in range(len(sentences) - window_size + 1):
            group = sentences[i:i + window_size]
            start = group[0]["start"]
            end = group[-1]["end"]

            # Skip if too short or too long
            if end - start < min_duration or end - start > max_duration:
                continue

            # CRITICAL: First sentence must be a standalone opening
            if not _is_standalone_opening(group[0]["text"]):
                continue

            text = " ".join(s["text"] for s in group)
            text = _normalize_transcript(text)

            # Must end with complete thought
            if not _ends_with_complete_thought(text):
                continue

            if text and len(text.split()) >= 15:
                windows.append({"start": start, "end": end, "text": text})

    return windows


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class _Scores:
    attention: float = 0.0
    curiosity: float = 0.0
    stakes: float = 0.0
    relevance: float = 0.0
    clarity: float = 5.0
    completeness: float = 0.0


def _score_segment(text: str, start_seconds: float) -> _Scores:
    """Score a text chunk on engagement dimensions."""
    scores = _Scores()
    words = text.split()

    # Attention (pattern interrupts, contrarian)
    scores.attention = min(_match_score(text, ATTENTION_PATTERNS), 10.0)
    # Short punchy first sentence bonus
    first_sent = re.split(r'[.!?]', text)[0]
    if 2 <= len(first_sent.split()) <= 6:
        scores.attention = min(scores.attention + 2.0, 10.0)
    # Negation list pattern ("It's not X. It's not Y.") — builds tension
    negation_count = len(re.findall(r"(?:it'?s not|not \w+ing)\b", text, re.I))
    if negation_count >= 2:
        scores.attention = min(scores.attention + 2.5, 10.0)
    # Percentage/number claims ("99% of people", "10x faster")
    if re.search(r'\b\d+%|\b\d+x\b', text, re.I):
        scores.attention = min(scores.attention + 1.5, 10.0)
    # Superlatives ("more than anything", "the best", "the worst")
    if re.search(r'\bmore than (?:anything|anyone|ever)\b', text, re.I):
        scores.attention = min(scores.attention + 1.5, 10.0)

    # Curiosity
    scores.curiosity = min(_match_score(text, CURIOSITY_PATTERNS), 10.0)
    if "?" in text:
        scores.curiosity = min(scores.curiosity + 1.5, 10.0)

    # Stakes
    scores.stakes = min(_match_score(text, STAKES_PATTERNS), 10.0)
    if _NUM_RE.search(text):
        scores.stakes = min(scores.stakes + 1.5, 10.0)

    # Viewer relevance
    you_count = len(_YOU_RE.findall(text))
    scores.relevance = min(you_count * 1.5, 4.0)
    scores.relevance += min(_match_score(text, IDENTITY_PATTERNS), 4.0)
    scores.relevance = min(scores.relevance, 10.0)

    # Standalone clarity — penalize fragments
    scores.clarity = 5.0
    if _ends_with_complete_sentence(text):
        scores.clarity += 3.0
    if text[0].isupper() if text else False:
        scores.clarity += 1.0
    if len(words) >= 6:
        scores.clarity += 1.0
    scores.clarity = min(scores.clarity, 10.0)

    # Thought completeness — does it convey a full idea?
    scores.completeness = 0.0
    if _ends_with_complete_sentence(text):
        scores.completeness += 5.0
    # Has both setup and payoff (e.g., claim + evidence, or question + tease)
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
    if len(sentences) >= 2:
        scores.completeness += 3.0
    elif len(sentences) == 1 and len(words) >= 8:
        scores.completeness += 1.5
    scores.completeness = min(scores.completeness, 10.0)

    return scores


def _compute_final_score(scores: _Scores, start_seconds: float, text: str) -> float:
    """Weighted combination of dimension scores."""
    # Weighted average
    final = (
        0.25 * scores.attention
        + 0.20 * scores.curiosity
        + 0.15 * scores.stakes
        + 0.15 * scores.relevance
        + 0.10 * scores.clarity
        + 0.15 * scores.completeness
    )

    # Temporal bonus: earlier hooks are more valuable for Shorts
    if start_seconds < 30:
        final += 1.5
    elif start_seconds < 90:
        final += 0.8
    elif start_seconds < 180:
        final += 0.3

    # Authority/story bonus
    auth = min(_match_score(text, AUTHORITY_PATTERNS), 3.0)
    story = min(_match_score(text, STORY_PATTERNS), 3.0)
    final += (auth + story) * 0.15

    return min(10.0, final)


# ═══════════════════════════════════════════════════════════════════════════════
# HOOK TYPE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def _classify_hook_type(text: str, scores: _Scores) -> tuple[str, str]:
    """Classify hook type and funnel role based on text and scores."""
    text_lower = text.lower()

    # Check specific patterns in priority order
    if _match_count(text, AUTHORITY_PATTERNS) >= 2:
        return "Authority", "Credibility"
    if any(p in text_lower for p in ["i was", "i used to", "years ago", "true story"]):
        return "Story-Based", "Engagement"
    if _match_count(text, ATTENTION_PATTERNS) >= 2 and scores.attention > 4:
        if any(p in text_lower for p in ["wrong", "mistake", "don't", "never"]):
            return "Contrarian", "Disruption"
        return "Pattern Interrupt", "Disruption"
    if scores.curiosity > 4:
        return "Curiosity Gap", "Retention"
    if scores.stakes > 4:
        if any(p in text_lower for p in ["mistake", "danger", "ruin", "warning", "risk"]):
            return "High Stakes Warning", "Urgency"
        return "Direct Benefit", "Conversion"
    if scores.relevance > 4:
        return "Personal Transformation", "Engagement"
    if "?" in text:
        return "Curiosity Gap", "Retention"
    if _match_score(text, BENEFIT_PATTERNS) > 3:
        return "Direct Benefit", "Conversion"

    return "Curiosity Gap", "Retention"


# ═══════════════════════════════════════════════════════════════════════════════
# INSIGHTS GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

_DYNAMICS_MAP = {
    "Curiosity Gap": "Curiosity hooks drive 2-3x higher click-through. The unresolved information gap keeps viewers watching to close the loop.",
    "Pattern Interrupt": "Pattern interrupts reset the scroll reflex by violating expectations. This format has the highest first-second retention on Shorts.",
    "High Stakes Warning": "Warning-framed content triggers urgency sharing — viewers share risk content 40% more than opportunity content.",
    "Authority": "Credibility signals in the first 3 seconds reduce skip rates by 25%. Authority hooks convert viewers to subscribers at 3x the rate.",
    "Story-Based": "Narrative hooks increase average watch time by 65%. Story openings sustain attention through the full Short.",
    "Direct Benefit": "Clear benefit hooks drive the highest save/bookmark rates. Viewers who see immediate value stay 2x longer.",
    "Contrarian": "Contrarian takes generate 3x more comments. This engagement signal boosts algorithmic distribution.",
    "Personal Transformation": "Transformation hooks work because viewers project themselves into the arc. They drive the highest 'watch again' rates.",
}

_PSYCHOLOGY_MAP = {
    "attention": "This hook exploits the orienting response — an involuntary reflex triggered by unexpected stimuli that forces the brain to pause.",
    "curiosity": "The Zeigarnik effect creates tension from incomplete information. Viewers feel compelled to continue watching.",
    "stakes": "Loss aversion makes threats feel 2x more intense than opportunities. The viewer's brain prioritizes processing this perceived risk.",
    "relevance": "Direct viewer address activates the self-referencing effect — personally relevant content gets encoded in memory more deeply.",
}

_TIP_MAP = {
    "attention": "Strengthen the opening: start with a shorter, punchier first sentence (3-5 words).",
    "curiosity": "Add an open loop: hint at information without revealing it. 'There's one thing that...' increases tension.",
    "stakes": "Quantify the stakes: '$50K mistake' hits harder than 'big mistake'. Add a concrete metric.",
    "relevance": "Add direct 'you' address or identity targeting ('If you're a creator...'). Make it personal.",
}


def _generate_insights(text: str, hook_type: str, scores: _Scores) -> tuple[str, str, str]:
    """Generate platform dynamics, viewer psychology, and improvement tip."""
    dims = {
        "attention": scores.attention,
        "curiosity": scores.curiosity,
        "stakes": scores.stakes,
        "relevance": scores.relevance,
    }
    strongest = max(dims, key=dims.get)
    weakest = min(dims, key=dims.get)

    dynamics = _DYNAMICS_MAP.get(hook_type, f"This {hook_type} hook shows strong engagement potential.")
    psychology = _PSYCHOLOGY_MAP.get(strongest, "This content triggers multiple engagement drivers simultaneously.")
    tip = _TIP_MAP.get(weakest, "Focus on making the opening line immediately compelling without requiring context.")

    return dynamics, psychology, tip


# ═══════════════════════════════════════════════════════════════════════════════
# SCORED SEGMENT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class _ScoredSegment:
    text: str
    start_seconds: float
    end_seconds: float
    final_score: float
    scores: _Scores
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
    Deterministic hook identification v5 (simplified) — no LLM calls.

    Pipeline:
    1. Parse transcript into timestamped segments
    2. Group segments into sentence-complete chunks (complete thoughts)
    3. Score each chunk on engagement signals
    4. Classify hook type
    5. Select top 5 non-overlapping, type-diverse hooks

    Core rule: Hooks must convey complete thoughts — never start or end mid-sentence.
    """

    def analyze(
        self, transcript: str, niche: str, language: str = "English",
        rules: list[dict] | None = None,
    ) -> HookEngineResult:
        logger.info("Running deterministic hook analysis v5 (simplified, no LLM)")

        # Step 1: Parse transcript
        segments = _parse_transcript_segments(transcript)
        if not segments:
            from app.exceptions import HookEngineError
            raise HookEngineError("Could not parse transcript into segments")

        # Step 2: Reconstruct sentences from fragments, then build hook windows
        sentences = _reconstruct_sentences(segments)
        if not sentences:
            sentences = segments  # fallback
        chunks = _build_hook_windows(sentences)
        if not chunks:
            chunks = sentences  # fallback
        logger.info("Built %d hook windows from %d sentences (%d raw segments)",
                     len(chunks), len(sentences), len(segments))

        # Get niche preferences
        niche_config = NICHES.get(niche, NICHES.get("Generic", {}))
        preferred_types = niche_config.get("preferredTypes", [])

        # Step 3: Score and classify each chunk
        scored: list[_ScoredSegment] = []
        for chunk in chunks:
            text = _normalize_transcript(chunk["text"])
            if not text or len(text.split()) < 4:
                continue

            # Reject filler (any filler signal disqualifies the hook)
            if _match_count(text, FILLER_PATTERNS) >= 1:
                continue

            scores = _score_segment(text, chunk["start"])
            hook_type, funnel_role = _classify_hook_type(text, scores)

            # Niche bonus
            niche_bonus = 0.8 if hook_type in preferred_types else 0.0
            final = _compute_final_score(scores, chunk["start"], text) + niche_bonus

            if final < 2.5:
                continue

            # Truncate at sentence boundary if too long
            display_text = text
            if len(display_text) > 300:
                # Find last sentence end before 300 chars
                last_end = -1
                for m in re.finditer(r'[.!?]', display_text[:300]):
                    last_end = m.end()
                if last_end > 50:
                    display_text = display_text[:last_end].rstrip()
                else:
                    display_text = display_text[:300].rstrip()

            scored.append(_ScoredSegment(
                text=display_text,
                start_seconds=chunk["start"],
                end_seconds=chunk["end"],
                final_score=min(10.0, final),
                scores=scores,
                hook_type=hook_type,
                funnel_role=funnel_role,
            ))

        # Sort by score
        scored.sort(key=lambda s: s.final_score, reverse=True)

        if not scored:
            from app.exceptions import HookEngineError
            raise HookEngineError("No hook candidates found in transcript")

        # Step 4: Select top 5 non-overlapping
        selected = self._select_top_5(scored, preferred_types)
        selected.sort(key=lambda s: s.final_score, reverse=True)

        # Step 5: Build output
        hooks = self._build_hook_candidates(selected)

        return HookEngineResult(
            hooks=hooks,
            provider="deterministic",
            model="rule-based-v5",
            attempts=1,
            input_tokens=None,
            output_tokens=None,
        )

    @staticmethod
    def _build_hook_candidates(selected: list[_ScoredSegment]) -> list[HookCandidate]:
        """Convert scored segments into HookCandidate objects."""
        hooks: list[HookCandidate] = []
        for rank, seg in enumerate(selected, 1):
            s = seg.scores
            score_dict = {
                "scroll_stop": round(s.attention, 1),
                "curiosity_gap": round(s.curiosity, 1),
                "stakes_intensity": round(s.stakes, 1),
                "emotional_voltage": round(s.relevance, 1),
                "standalone_clarity": round(s.clarity, 1),
                "thematic_focus": 5.0,  # neutral — not scored in simplified engine
                "thought_completeness": round(s.completeness, 1),
            }

            dynamics, psychology, tip = _generate_insights(seg.text, seg.hook_type, seg.scores)

            hooks.append(HookCandidate(
                rank=rank,
                hook_text=seg.text,
                start_time=_seconds_to_timestamp(seg.start_seconds),
                end_time=_seconds_to_timestamp(seg.end_seconds),
                start_seconds=seg.start_seconds,
                end_seconds=seg.end_seconds,
                hook_type=seg.hook_type,
                funnel_role=seg.funnel_role,
                scores=score_dict,
                attention_score=round(seg.final_score, 1),
                platform_dynamics=dynamics,
                viewer_psychology=psychology,
                improvement_suggestion=tip,
                is_composite=False,
            ))
        return hooks

    def _select_top_5(
        self, candidates: list[_ScoredSegment], preferred_types: list[str],
    ) -> list[_ScoredSegment]:
        """Select top 5 non-overlapping hooks with type diversity."""
        selected: list[_ScoredSegment] = []
        types_used: set[str] = set()

        for c in candidates:
            if len(selected) >= 5:
                break
            if not any(self._overlaps(c, s) for s in selected):
                selected.append(c)
                types_used.add(c.hook_type)

        # Diversity pass: swap weakest duplicate with new type if < 3 types
        if len(types_used) < 3 and len(selected) >= 3:
            for c in candidates:
                if c.hook_type in types_used or c in selected:
                    continue
                if any(self._overlaps(c, s) for s in selected):
                    continue
                type_counts = {}
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

        # Fill remaining slots
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
