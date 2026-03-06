def title_from_hook_text(hook_text: str) -> str:
    """Generate a fallback title from the first words of hook text."""
    words = hook_text.split()
    title = " ".join(words[:8])
    if len(words) > 8:
        title = title.rstrip(".,;:!?") + "..."
    return title[:60] if title else "Short"
