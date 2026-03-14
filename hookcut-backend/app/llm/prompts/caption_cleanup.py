import re


def sanitize_for_prompt(text: str, max_len: int = 500) -> str:
    """Strip control characters from LLM output before re-embedding in another prompt."""
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return cleaned[:max_len]


def build_caption_cleanup_prompt(hook_text: str, language: str = "English") -> str:
    """Build prompt for cleaning transcript text for Short captions."""
    safe_hook_text = sanitize_for_prompt(hook_text)
    return f"""Clean this transcript segment for YouTube Short captions.

Rules:
- Fix punctuation and capitalization
- Remove verbal fillers (um, uh, like, you know, basically, right, so)
- Remove false starts and repeated words
- Keep the ORIGINAL language — NEVER translate
- Keep technical terms and proper nouns exactly as spoken
- Keep code-switching (mixing languages) as-is
- Output clean text only, no timestamps, no labels
- Do not add or invent any words not in the original

Language: {language}

Segment:
{safe_hook_text}"""


def build_title_generation_prompt(
    hook_text: str,
    niche: str,
    language: str = "English",
    hook_type: str = "",
    attention_score: float = 0.0,
    video_title: str = "",
) -> str:
    """Build prompt for generating a catchy, Short-optimized title."""
    safe_hook_text = sanitize_for_prompt(hook_text) if hook_text else ""
    hook_type_line = f"Hook type: {hook_type}\n" if hook_type else ""
    score_line = f"Hook score: {attention_score:.1f}/10\n" if attention_score else ""
    video_title_line = f"Video title: {sanitize_for_prompt(video_title, max_len=200)}\n" if video_title else ""

    transcript_block = f"\nHook transcript:\n{safe_hook_text}" if safe_hook_text else ""

    return f"""You are a viral YouTube Shorts title writer. Generate ONE punchy, scroll-stopping title for this Short.

Niche: {niche}
Language: {language}
{video_title_line}{hook_type_line}{score_line}
What makes a great Shorts title:
- Creates instant curiosity or promises a clear, specific payoff
- Uses concrete numbers or specifics where possible ("3 seconds", "$10k", "5 years")
- Feels conversational — like something a person would actually say out loud
- Front-loads the most interesting part (first 3 words must hook)
- Under 60 characters so it doesn't get cut off
- Title case or sentence case only (no ALL CAPS shouting)
- Match the spoken language — if hook is in Hindi, title must be in Hindi
- No generic phrases ("You won't believe...", "This is crazy...", "Must watch")
- No emojis
- Output ONLY the title text — no quotes, no explanation
{transcript_block}"""
