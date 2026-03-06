#!/usr/bin/env python3
"""
Generate best-frame thumbnails for HookCut shorts.

Picks the most visually interesting frame using FFmpeg's thumbnail filter
(analyzes histogram diversity across frame batches) then applies a subtle
contrast/saturation lift to make it pop.

Usage:
    # Re-generate thumbnails for ALL ready shorts missing a thumbnail
    python scripts/generate_thumbnails.py

    # Re-generate for specific short IDs
    python scripts/generate_thumbnails.py <short_id> [<short_id> ...]

    # Re-generate even if thumbnail already exists
    python scripts/generate_thumbnails.py --force
"""

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path

# Ensure app root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.dependencies import get_db_session
from app.models.session import Short
from app.services.storage import StorageService
from app.utils.ffmpeg_commands import extract_thumbnail
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


def _get_local_video_path(storage: StorageService, video_file_key: str) -> str | None:
    """Resolve the local file path for a stored video key."""
    if not video_file_key:
        return None
    try:
        local_path = storage._safe_local_path(video_file_key)
        return local_path if os.path.exists(local_path) else None
    except Exception:
        return None


def regenerate_thumbnail(short: Short, storage: StorageService, force: bool = False) -> bool:
    """
    Extract the best frame from a short's video and upload as thumbnail.
    Returns True on success.
    """
    if short.thumbnail_file_key and not force:
        logger.info("  Skipping %s — thumbnail already exists (use --force to overwrite)", short.id[:8])
        return False

    if not short.video_file_key:
        logger.warning("  Skipping %s — no video_file_key", short.id[:8])
        return False

    video_path = _get_local_video_path(storage, short.video_file_key)
    if not video_path:
        logger.warning("  Skipping %s — video file not found locally: %s", short.id[:8], short.video_file_key)
        return False

    with tempfile.TemporaryDirectory(prefix=f"thumb_{short.id[:8]}_") as tmp:
        thumb_path = os.path.join(tmp, "thumbnail.jpg")
        result = extract_thumbnail(video_path, thumb_path)

        if not result.success:
            logger.error("  Failed for %s: %s", short.id[:8], result.error)
            return False

        thumb_key = f"shorts/{short.id}/thumbnail.jpg"
        storage.upload(thumb_path, thumb_key)
        return thumb_key


def main():
    parser = argparse.ArgumentParser(description="Generate thumbnails for HookCut shorts")
    parser.add_argument("short_ids", nargs="*", help="Specific short IDs to process (default: all ready shorts)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing thumbnails")
    args = parser.parse_args()

    db = get_db_session()
    storage = StorageService()

    try:
        if args.short_ids:
            shorts = [db.get(Short, sid) for sid in args.short_ids]
            shorts = [s for s in shorts if s is not None]
            not_found = [sid for sid, s in zip(args.short_ids, shorts) if s is None]
            for sid in not_found:
                logger.warning("Short not found: %s", sid)
        else:
            query = select(Short).where(Short.status == "ready", Short.video_file_key.isnot(None))
            if not args.force:
                query = query.where(Short.thumbnail_file_key.is_(None))
            shorts = db.execute(query).scalars().all()

        if not shorts:
            logger.info("No shorts to process.")
            return

        logger.info("Processing %d short(s)...", len(shorts))
        success, skipped, failed = 0, 0, 0

        for short in shorts:
            logger.info("[%s] hook: %s...", short.id[:8], (short.hook.hook_text[:60] if short.hook else "?"))
            result = regenerate_thumbnail(short, storage, force=args.force)

            if result is False:
                skipped += 1
            elif result:
                short.thumbnail_file_key = result
                db.commit()
                logger.info("  ✓ Saved thumbnail: %s", result)
                success += 1
            else:
                failed += 1

        logger.info("\nDone — %d succeeded, %d skipped, %d failed", success, skipped, failed)

    finally:
        db.close()


if __name__ == "__main__":
    main()
