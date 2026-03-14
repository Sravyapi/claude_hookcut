#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch hook generator - runs HookEngine on all transcripts for a given prompt version.

Usage:
    python hook_generator.py <prompt_version>             # Generate for all videos with transcripts
    python hook_generator.py <prompt_version> --video-id X  # Generate for one video
    python hook_generator.py register <version> <description>  # Register a new prompt version
"""

import hashlib
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _EVAL_DIR.parent.parent
sys.path.insert(0, str(_EVAL_DIR))
sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(_BACKEND_DIR / ".env")

from db import get_db, insert_hook, insert_prompt_version


def register_prompt_version(version: str, description: str, parent: str | None = None):
    """Register a new prompt version by capturing the current prompt text."""
    from app.llm.prompts.hook_identification import build_hook_prompt
    prompt_text = build_hook_prompt("Generic", "[PLACEHOLDER]", "English")
    prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]

    with get_db() as conn:
        insert_prompt_version(
            conn,
            version=version,
            description=description,
            prompt_hash=prompt_hash,
            prompt_snapshot=prompt_text,
            parent_version=parent,
        )
    print(f"Registered prompt version '{version}' (hash: {prompt_hash})")


def generate_hooks_for_video(video_id: str, prompt_version: str, max_rate_limit_retries: int = 3) -> bool:
    """Run HookEngine on a single video. Returns True on success.

    Handles Gemini 429 rate limits with 60s backoff.
    """
    import time as _time
    from app.services.hook_engine import HookEngine

    with get_db() as conn:
        transcript = conn.execute(
            "SELECT text FROM transcripts WHERE video_id=? AND text IS NOT NULL",
            (video_id,),
        ).fetchone()
        if not transcript:
            print(f"  ✗ No transcript for {video_id}")
            return False

        video = conn.execute("SELECT niche FROM videos WHERE video_id=?", (video_id,)).fetchone()
        niche = video["niche"] if video else "Generic"

    for rate_retry in range(max_rate_limit_retries):
        try:
            engine = HookEngine()
            result = engine.analyze(
                transcript=transcript["text"],
                niche=niche,
                language="English",
            )
            break  # success
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                wait = 65 * (rate_retry + 1)
                print(f"  ⏳ Rate limited — waiting {wait}s (retry {rate_retry + 1}/{max_rate_limit_retries})...")
                _time.sleep(wait)
                if rate_retry == max_rate_limit_retries - 1:
                    print(f"  ✗ Rate limit persists after {max_rate_limit_retries} retries for {video_id}")
                    return False
                continue
            else:
                print(f"  ✗ HookEngine error: {e}")
                return False

    with get_db() as conn:
        for h in result.hooks:
            insert_hook(
                conn,
                video_id=video_id,
                prompt_version=prompt_version,
                rank=h.rank,
                hook_text=h.hook_text,
                start_time=h.start_time,
                end_time=h.end_time,
                start_seconds=h.start_seconds,
                end_seconds=h.end_seconds,
                duration_seconds=h.end_seconds - h.start_seconds,
                hook_type=h.hook_type,
                funnel_role=h.funnel_role,
                cognitive_tension=h.cognitive_tension,
                scores=h.scores,
                attention_score=h.attention_score,
                virality_score=h.virality_score,
                justification=h.justification,
                algorithm_dynamics=h.algorithm_dynamics,
                viewer_psychology=h.viewer_psychology,
                improvement_suggestion=h.improvement_suggestion,
                is_composite=h.is_composite,
            )
    print(f"  ✓ {len(result.hooks)} hooks generated via {result.provider} ({result.attempts} attempt(s))")
    return True


def generate_all(prompt_version: str):
    """Generate hooks for all videos with transcripts that don't have hooks yet."""
    with get_db() as conn:
        # Verify prompt version exists
        pv = conn.execute("SELECT * FROM prompt_versions WHERE version=?", (prompt_version,)).fetchone()
        if not pv:
            print(f"ERROR: Prompt version '{prompt_version}' not registered. Run: python hook_generator.py register {prompt_version} 'description'")
            return

        videos = conn.execute(
            """SELECT v.video_id, v.title, v.creator_name
               FROM videos v
               JOIN transcripts t ON v.video_id = t.video_id
               WHERE t.text IS NOT NULL
                 AND v.video_id NOT IN (
                     SELECT video_id FROM hooks WHERE prompt_version = ?
                 )
               ORDER BY v.review_order""",
            (prompt_version,),
        ).fetchall()

    total = len(videos)
    print(f"Generating hooks for {total} videos (prompt: {prompt_version})...\n")

    import time

    success = 0
    failed = 0
    consecutive_failures = 0
    # Gemini free tier: 20 req/min. Each video uses 1-3 requests.
    # Pace at ~5 videos/min (12s gap) to stay safely under limit.
    PACE_DELAY = 12

    for i, v in enumerate(videos, 1):
        print(f"[{i}/{total}] {v['creator_name']} - {v['title'][:60]}...")
        if generate_hooks_for_video(v["video_id"], prompt_version):
            success += 1
            consecutive_failures = 0
        else:
            failed += 1
            consecutive_failures += 1
            if consecutive_failures >= 3:
                print(f"  [!] 3 consecutive failures - waiting 65s for rate limit...")
                time.sleep(65)
                consecutive_failures = 0
                continue

        # Pace to avoid rate limits
        if i < total:
            time.sleep(PACE_DELAY)

        # Progress checkpoint every 50 videos
        if i % 50 == 0:
            print(f"\n  --- Checkpoint: {success} success, {failed} failed, {total - i} remaining ---\n")

    print(f"\nDone: {success} success, {failed} failed out of {total}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "register":
        if len(sys.argv) < 4:
            print("Usage: python hook_generator.py register <version> <description> [parent_version]")
            sys.exit(1)
        parent = sys.argv[4] if len(sys.argv) > 4 else None
        register_prompt_version(sys.argv[2], sys.argv[3], parent)
    elif len(sys.argv) > 2 and sys.argv[2] == "--video-id":
        generate_hooks_for_video(sys.argv[3], sys.argv[1])
    else:
        generate_all(sys.argv[1])
