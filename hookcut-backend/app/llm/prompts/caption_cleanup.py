def build_caption_cleanup_prompt(hook_text: str, language: str = "English") -> str:
    """Build prompt for cleaning transcript text for Short captions."""
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
{hook_text}"""


def build_title_generation_prompt(
    hook_text: str, niche: str, language: str = "English"
) -> str:
    """Build prompt for generating a Short-optimized title."""
    return f"""Generate a YouTube Shorts title for this hook segment.

Niche: {niche}
Language: {language}

Rules:
- Under 60 characters
- No clickbait or misleading claims
- No ALL CAPS (title case or sentence case only)
- Match the content language (if hook is in Hindi, title should be in Hindi)
- Include a curiosity hook or benefit statement
- No emojis unless they add genuine value
- Output ONLY the title text, nothing else

Hook:
{hook_text}"""
