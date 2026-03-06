#!/usr/bin/env python3
"""
Generate catchy titles for HookCut shorts using the LLM.

Uses hook text, hook type, attention score, niche, and language to produce
scroll-stopping titles that are specific, front-loaded, and under 60 chars.

Usage:
    # Generate titles for ALL ready shorts with no title
    python scripts/generate_titles.py

    # Generate for specific short IDs
    python scripts/generate_titles.py <short_id> [<short_id> ...]

    # Re-generate even if a title already exists
    python scripts/generate_titles.py --force

    # Preview only — don't save to DB
    python scripts/generate_titles.py --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.dependencies import get_db_session
from app.llm.provider import get_provider
from app.llm.prompts.caption_cleanup import build_title_generation_prompt
from app.models.session import Short
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def generate_title_for_short(short: Short) -> str:
    """Call LLM to generate a catchy title for a short."""
    hook = short.hook
    session = short.session

    hook_text = hook.hook_text if hook else ""
    niche = session.niche if session else "Generic"
    language = session.language if session else "English"
    hook_type = hook.hook_type if hook else ""
    attention_score = hook.attention_score if hook else 0.0

    settings = get_settings()
    provider = get_provider(settings.LLM_PRIMARY_PROVIDER)

    prompt = build_title_generation_prompt(
        hook_text=hook_text,
        niche=niche,
        language=language,
        hook_type=hook_type,
        attention_score=attention_score,
    )

    response = provider.generate(prompt, max_tokens=100)
    title = response.text.strip().strip('"').strip("'")
    if not title:
        words = hook_text.split()
        title = " ".join(words[:8])
        if len(words) > 8:
            title = title.rstrip(".,;:!?") + "..."
    return title[:60]


def main():
    parser = argparse.ArgumentParser(description="Generate titles for HookCut shorts")
    parser.add_argument("short_ids", nargs="*", help="Specific short IDs (default: all ready shorts without title)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing titles")
    parser.add_argument("--dry-run", action="store_true", help="Print titles without saving to DB")
    args = parser.parse_args()

    db = get_db_session()

    try:
        if args.short_ids:
            shorts = [db.get(Short, sid) for sid in args.short_ids]
            not_found = [sid for sid, s in zip(args.short_ids, shorts) if s is None]
            shorts = [s for s in shorts if s is not None]
            for sid in not_found:
                logger.warning("Short not found: %s", sid)
        else:
            query = select(Short).where(Short.status == "ready")
            if not args.force:
                query = query.where(Short.title.is_(None))
            shorts = db.execute(query).scalars().all()

        if not shorts:
            logger.info("No shorts to process.")
            return

        logger.info("Generating titles for %d short(s)...\n", len(shorts))
        success, failed = 0, 0

        for short in shorts:
            hook_preview = (short.hook.hook_text[:70] + "…") if short.hook else "?"
            logger.info("[%s] %s", short.id[:8], hook_preview)

            if short.title and not args.force:
                logger.info("  Current: %s (use --force to regenerate)\n", short.title)
                continue

            try:
                title = generate_title_for_short(short)
                if args.dry_run:
                    logger.info("  → %s  [dry-run, not saved]\n", title)
                else:
                    short.title = title
                    db.commit()
                    logger.info("  → %s  ✓\n", title)
                success += 1
            except Exception as e:
                logger.error("  Failed: %s\n", e)
                failed += 1

        action = "previewed" if args.dry_run else "saved"
        logger.info("Done — %d %s, %d failed", success, action, failed)

    finally:
        db.close()


if __name__ == "__main__":
    main()
