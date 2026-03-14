#!/usr/bin/env python3
"""
Top-up: fetch N additional videos from specific creators to reach 400 English train videos.
Skips any video IDs already in the DB.
"""
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from googleapiclient.discovery import build as yt_build
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from db import get_db, insert_video
from dataset_builder import (
    _get_uploads_playlist_id,
    _fetch_all_video_ids,
    _fetch_video_details,
)

TARGETS = {
    "Finance": [
        ("Asset Yogi", 1),
        ("Zerodha", 1),
        ("Wint Wealth", 1),
        ("Shankar Nath", 1),
        ("freefincal", 1),
        ("ET Money", 1),
        ("Prateek Singh", 1),
    ],
    "Podcast": [
        ("Humans of Bombay", 5),
        ("Bhuvan Bam Podcast", 1),
        ("Barbershop", 1),
        ("Cyrus Says", 1),
        ("Indian Silicon Valley", 1),
    ],
    "Education": [
        ("Intellipaat", 1),
        ("Simplilearn", 1),
        ("Dhruv Rathee", 1),
        ("edureka", 1),
        ("Neso Academy", 1),
        ("Great Learning", 1),
    ],
}


def _pick_diverse(candidates: list[dict], n: int, already_used: set[str]) -> list[dict]:
    """Pick n videos not already in the DB, preferring ones not yet represented by category."""
    pool = [v for v in candidates if v["video_id"] not in already_used]
    if not pool:
        return []
    # Prefer videos whose performance_category isn't already saturated
    # Just pick highest-velocity ones not already fetched
    pool_sorted = sorted(pool, key=lambda x: x["views_per_day"], reverse=True)
    return pool_sorted[:n]


def run():
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print("ERROR: YOUTUBE_API_KEY missing")
        sys.exit(1)
    yt = yt_build("youtube", "v3", developerKey=key)

    added_total = 0

    for niche, creator_targets in TARGETS.items():
        print(f"\n{'='*50}")
        print(f"Niche: {niche}")
        print(f"{'='*50}")

        for creator_name, n_wanted in creator_targets:
            with get_db() as conn:
                creator = conn.execute(
                    "SELECT * FROM creators WHERE name=? AND niche=?",
                    (creator_name, niche),
                ).fetchone()
                if not creator:
                    print(f"  ✗ Creator not found: {creator_name}")
                    continue

                existing_ids = set(
                    r["video_id"]
                    for r in conn.execute(
                        "SELECT video_id FROM videos WHERE creator_id=?",
                        (creator["id"],),
                    ).fetchall()
                )

            print(f"\n  {creator_name} — fetching (need {n_wanted} new, already have {len(existing_ids)})")

            try:
                playlist_id = _get_uploads_playlist_id(yt, creator["channel_id"])
                if not playlist_id:
                    print(f"    ✗ No uploads playlist")
                    continue

                video_ids = _fetch_all_video_ids(yt, playlist_id, max_results=200)
                details = _fetch_video_details(yt, video_ids)
                long_form = [d for d in details if d["duration_seconds"] >= 180]

                picks = _pick_diverse(long_form, n_wanted, existing_ids)
                if not picks:
                    print(f"    ✗ No new videos found")
                    continue

                with get_db() as conn:
                    for v in picks:
                        # Assign performance_category based on velocity rank in full pool
                        by_vel = sorted(long_form, key=lambda x: x["views_per_day"], reverse=True)
                        rank = next((i for i, x in enumerate(by_vel) if x["video_id"] == v["video_id"]), 0)
                        total = max(len(by_vel), 1)
                        if rank / total < 0.33:
                            cat = "best"
                        elif rank / total < 0.66:
                            cat = "mid"
                        else:
                            cat = "recent"

                        insert_video(
                            conn,
                            video_id=v["video_id"],
                            creator_id=creator["id"],
                            title=v["title"],
                            url=f"https://www.youtube.com/watch?v={v['video_id']}",
                            views=v["views"],
                            likes=v["likes"],
                            comments=v["comments"],
                            published_at=v["published_at"],
                            duration_seconds=v["duration_seconds"],
                            views_per_day=v["views_per_day"],
                            performance_category=cat,
                            dataset_split="train",
                            niche=niche,
                            creator_name=creator_name,
                            content_language="English",
                        )
                        added_total += 1
                        print(f"    ✓ [{cat}] {v['title'][:70]}")

            except Exception as e:
                print(f"    ✗ Error: {e}")

    print(f"\n{'='*50}")
    print(f"Done. Added {added_total} videos.")

    # Re-run round-robin review_order for English train videos
    print("\nReassigning review_order...")
    _reassign_review_order()


def _reassign_review_order():
    with get_db() as conn:
        rows = conn.execute(
            """SELECT video_id, niche, performance_category, creator_name
               FROM videos
               WHERE dataset_split='train' AND COALESCE(content_language,'English')='English'
               ORDER BY niche,
                        CASE performance_category WHEN 'best' THEN 0 WHEN 'mid' THEN 1 ELSE 2 END,
                        creator_name"""
        ).fetchall()

        videos_by_niche = {}
        for r in rows:
            n = r["niche"]
            if n not in videos_by_niche:
                videos_by_niche[n] = []
            videos_by_niche[n].append(r["video_id"])

        niche_order = sorted(videos_by_niche.keys(), key=lambda n: len(videos_by_niche[n]))
        queues = {n: list(videos_by_niche[n]) for n in niche_order}

        interleaved = []
        while any(queues[n] for n in niche_order):
            for n in niche_order:
                if queues[n]:
                    interleaved.append(queues[n].pop(0))

        for i, vid in enumerate(interleaved, start=1):
            conn.execute("UPDATE videos SET review_order=? WHERE video_id=?", (i, vid))
        conn.commit()

    print(f"  ✓ Assigned review_order to {len(interleaved)} English train videos")

    # Print batch summary
    batch_size = max(1, math.ceil(len(interleaved) * 10 / 100))
    niches = sorted(videos_by_niche.keys())
    print(f"  Batch size: {batch_size}, Total batches: {math.ceil(len(interleaved)/batch_size)}")
    for b in range(1, 4):
        start = (b - 1) * batch_size
        end = min(start + batch_size, len(interleaved))
        batch = interleaved[start:end]
        with get_db() as conn:
            ph = ",".join("?" * len(batch))
            nc = {r["niche"]: r["cnt"] for r in conn.execute(
                f"SELECT niche, COUNT(*) as cnt FROM videos WHERE video_id IN ({ph}) GROUP BY niche", batch
            ).fetchall()}
        missing = [n for n in niches if n not in nc]
        flag = f" ⚠️ missing: {missing}" if missing else " ✓"
        print(f"  Batch {b} ({len(batch)}): {dict(sorted(nc.items()))}{flag}")


if __name__ == "__main__":
    run()
