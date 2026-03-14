#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Print videos that need hooks for a given prompt version.

Usage:
    python get_pending.py                    # v1-pro, all English train videos
    python get_pending.py v1-flash           # Flash model
    python get_pending.py v1-pro --json      # JSON output for scripting
    python get_pending.py v1-pro --limit 10  # first 10 only

Each row printed includes: video_id | niche | creator_name | title
Also prints the clipboard-ready context string (Niche: X, Creator: Y, Title: Z)
"""

import json
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_EVAL_DIR))

from db import get_db


def get_pending(prompt_version: str = "v1-pro", limit: int = 0) -> list[dict]:
    with get_db() as conn:
        q = """
            SELECT v.video_id, v.creator_name, v.title, v.niche,
                   v.review_order, v.views, v.duration_seconds,
                   COALESCE(v.content_language, 'English') as lang,
                   t.char_count
            FROM videos v
            JOIN transcripts t ON v.video_id = t.video_id
            WHERE v.dataset_split = 'train'
              AND t.text IS NOT NULL
              AND COALESCE(v.content_language, 'English') = 'English'
              AND v.video_id NOT IN (
                  SELECT video_id FROM hooks WHERE prompt_version = ?
              )
            ORDER BY v.review_order
        """
        args = [prompt_version]
        if limit > 0:
            q += f" LIMIT {limit}"
        rows = conn.execute(q, args).fetchall()
        return [dict(r) for r in rows]


def build_context_prefix(video: dict) -> str:
    """Build the niche/creator/title context prefix to prepend to transcript."""
    return (
        f"Niche: {video['niche']}\n"
        f"Creator: {video['creator_name']}\n"
        f"Title: {video['title']}\n\n"
        f"TRANSCRIPT:\n"
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("version", nargs="?", default="v1-pro")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    videos = get_pending(args.version, args.limit)

    if args.as_json:
        print(json.dumps(videos, indent=2))
        sys.exit(0)

    if not videos:
        print(f"✓ No pending videos for {args.version}")
        sys.exit(0)

    print(f"\n{'='*70}")
    print(f"  Pending hooks for: {args.version}  ({len(videos)} videos)")
    print(f"{'='*70}\n")
    for i, v in enumerate(videos, 1):
        dur = v['duration_seconds'] or 0
        m, s = divmod(int(dur), 60)
        chars = v.get('char_count', 0) or 0
        print(f"[{i:3d}] {v['video_id']}  {v['niche']:20s}  {v['creator_name'][:28]:28s}  {m}:{s:02d}  ~{chars//4:,} tok")
        print(f"       Title: {v['title'][:70]}")
        print()

    print(f"Total: {len(videos)} videos need hooks for {args.version}")
    print()
    print("Context prefix format:")
    print("  Niche: <niche>")
    print("  Creator: <creator_name>")
    print("  Title: <title>")
    print()
    print("  TRANSCRIPT:")
    print("  [transcript text]")
