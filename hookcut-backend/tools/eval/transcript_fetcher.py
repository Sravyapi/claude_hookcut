#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch transcript fetcher - downloads transcripts for all videos in the dataset.

Usage:
    python transcript_fetcher.py              # Fetch all missing transcripts
    python transcript_fetcher.py --video-id X # Fetch one specific video
"""

import sys
from pathlib import Path

# Add eval dir + backend dir to path
_EVAL_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _EVAL_DIR.parent.parent
sys.path.insert(0, str(_EVAL_DIR))
sys.path.insert(0, str(_BACKEND_DIR))

from config import TRANSCRIPTS_DIR
from db import get_db, insert_transcript


def fetch_transcript_for_video(video_id: str) -> tuple[str | None, str | None, str | None]:
    """Fetch transcript using HookCut's TranscriptService. Returns (text, provider, error)."""
    try:
        from dotenv import load_dotenv
        load_dotenv(_BACKEND_DIR / ".env")

        from app.services.transcript import TranscriptService

        svc = TranscriptService()
        result = svc.fetch(video_id, language="English")
        if result and result.text:
            return result.text, result.provider, None
        return None, None, "No transcript returned"
    except Exception as e:
        return None, None, str(e)


def save_transcript_file(video_id: str, text: str) -> str:
    """Save transcript to file, return path."""
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    path = TRANSCRIPTS_DIR / f"{video_id}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def fetch_all_missing():
    """Fetch transcripts for all videos that don't have one yet."""
    with get_db() as conn:
        videos = conn.execute(
            """SELECT v.video_id, v.title, v.creator_name, v.niche
               FROM videos v
               LEFT JOIN transcripts t ON v.video_id = t.video_id
               WHERE t.id IS NULL
               ORDER BY v.review_order"""
        ).fetchall()

    total = len(videos)
    print(f"Fetching transcripts for {total} videos...\n")

    success = 0
    failed = 0

    for i, v in enumerate(videos, 1):
        vid = v["video_id"]
        print(f"[{i}/{total}] {v['creator_name']} — {v['title'][:60]}...")

        text, provider, error = fetch_transcript_for_video(vid)

        with get_db() as conn:
            if text:
                file_path = save_transcript_file(vid, text)
                insert_transcript(conn, video_id=vid, text=text, provider=provider, file_path=file_path)
                conn.execute(
                    "UPDATE videos SET transcript_path=? WHERE video_id=?",
                    (file_path, vid),
                )
                print(f"  ✓ {len(text):,} chars via {provider}")
                success += 1
            else:
                insert_transcript(conn, video_id=vid, text=None, provider=None, file_path=None, error=error)
                print(f"  ✗ {error}")
                failed += 1

    print(f"\nDone: {success} success, {failed} failed out of {total}")


def fetch_one(video_id: str):
    """Fetch transcript for a single video."""
    print(f"Fetching transcript for {video_id}...")
    text, provider, error = fetch_transcript_for_video(video_id)
    if text:
        file_path = save_transcript_file(video_id, text)
        with get_db() as conn:
            insert_transcript(conn, video_id=video_id, text=text, provider=provider, file_path=file_path)
            conn.execute("UPDATE videos SET transcript_path=? WHERE video_id=?", (file_path, video_id))
        print(f"✓ {len(text):,} chars via {provider} → {file_path}")
    else:
        with get_db() as conn:
            insert_transcript(conn, video_id=video_id, text=None, provider=None, file_path=None, error=error)
        print(f"✗ {error}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--video-id":
        fetch_one(sys.argv[2])
    else:
        fetch_all_missing()
