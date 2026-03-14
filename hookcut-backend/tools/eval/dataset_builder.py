#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Builder - Populates creators + videos via YouTube Data API v3.

Usage:
    python dataset_builder.py seed          # Load seed creators into DB
    python dataset_builder.py enrich        # Fetch channel IDs + subscriber counts via API
    python dataset_builder.py fetch-videos  # Fetch videos for all creators
    python dataset_builder.py split         # Assign train/test split + review order
    python dataset_builder.py export        # Export to Excel spreadsheet
    python dataset_builder.py all           # Run all steps in order
"""

import json
import math
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path for config imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from googleapiclient.discovery import build as yt_build

from config import DEFAULT_CONFIG, EVAL_DIR
from db import get_db, insert_creator, insert_video
from seed_creators import SEED_CREATORS


def _get_youtube_client():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print("ERROR: YOUTUBE_API_KEY not found in environment or .env")
        sys.exit(1)
    return yt_build("youtube", "v3", developerKey=key)


# ── Step 1: Seed creators ──────────────────────────────────────────────

def seed_creators():
    """Insert seed creator list into DB."""
    cfg = DEFAULT_CONFIG
    with get_db() as conn:
        for c in SEED_CREATORS:
            niche = c["niche"]
            if niche not in cfg.niches:
                print(f"  SKIP: {c['name']} — niche '{niche}' not in config")
                continue
            insert_creator(
                conn,
                name=c["name"],
                handle=c.get("handle"),
                channel_id=c.get("channel_id"),
                niche=niche,
                tier=c["tier"],
                country=cfg.creator_country,
                audience_country=cfg.audience_country,
                content_language=cfg.content_language,
            )
    print(f"Seeded {len(SEED_CREATORS)} creators.")


# ── Step 2: Enrich via YouTube API ─────────────────────────────────────

def enrich_creators():
    """Resolve channel IDs and subscriber counts via YouTube API."""
    yt = _get_youtube_client()

    with get_db() as conn:
        creators = conn.execute(
            "SELECT id, name, handle, channel_id FROM creators WHERE channel_id IS NULL OR subscriber_count IS NULL"
        ).fetchall()

        for c in creators:
            cid = c["channel_id"]
            try:
                if not cid and c["handle"]:
                    # Search by handle
                    handle = c["handle"].lstrip("@")
                    resp = yt.search().list(
                        q=handle, type="channel", maxResults=1, part="snippet"
                    ).execute()
                    items = resp.get("items", [])
                    if items:
                        cid = items[0]["snippet"]["channelId"]

                if not cid:
                    # Search by name
                    resp = yt.search().list(
                        q=c["name"], type="channel", maxResults=1, part="snippet"
                    ).execute()
                    items = resp.get("items", [])
                    if items:
                        cid = items[0]["snippet"]["channelId"]

                if cid:
                    # Get channel details
                    ch_resp = yt.channels().list(
                        id=cid, part="statistics,snippet"
                    ).execute()
                    ch_items = ch_resp.get("items", [])
                    if ch_items:
                        stats = ch_items[0]["statistics"]
                        snippet = ch_items[0]["snippet"]
                        subs = int(stats.get("subscriberCount", 0))
                        url = f"https://www.youtube.com/channel/{cid}"
                        conn.execute(
                            """UPDATE creators SET channel_id=?, subscriber_count=?,
                               channel_url=? WHERE id=?""",
                            (cid, subs, url, c["id"]),
                        )
                        print(f"  ✓ {c['name']}: {subs:,} subs")
                    else:
                        print(f"  ✗ {c['name']}: channel details not found")
                else:
                    print(f"  ✗ {c['name']}: channel not found")
            except Exception as e:
                print(f"  ✗ {c['name']}: API error — {e}")


# ── Step 3: Fetch videos ──────────────────────────────────────────────

def _get_uploads_playlist_id(yt, channel_id: str) -> str | None:
    resp = yt.channels().list(id=channel_id, part="contentDetails").execute()
    items = resp.get("items", [])
    if items:
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    return None


def _fetch_all_video_ids(yt, playlist_id: str, max_results: int = 300) -> list[str]:
    """Fetch video IDs from uploads playlist (cheap: 1 unit per 50 items)."""
    video_ids = []
    page_token = None
    while len(video_ids) < max_results:
        resp = yt.playlistItems().list(
            playlistId=playlist_id,
            part="contentDetails",
            maxResults=50,
            pageToken=page_token,
        ).execute()
        for item in resp.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return video_ids[:max_results]


def _fetch_video_details(yt, video_ids: list[str]) -> list[dict]:
    """Batch fetch video statistics + snippet (50 per API call)."""
    all_details = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        resp = yt.videos().list(
            id=",".join(batch),
            part="statistics,snippet,contentDetails",
        ).execute()
        for item in resp.get("items", []):
            stats = item["statistics"]
            snippet = item["snippet"]
            # Parse duration (ISO 8601 PT format)
            dur_str = item["contentDetails"]["duration"]
            duration_s = _parse_iso_duration(dur_str)
            published = snippet["publishedAt"]
            views = int(stats.get("viewCount", 0))
            # Calculate views per day
            pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
            days_since = max(1, (datetime.now(timezone.utc) - pub_date).days)
            all_details.append({
                "video_id": item["id"],
                "title": snippet["title"],
                "published_at": published,
                "views": views,
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "duration_seconds": duration_s,
                "views_per_day": round(views / days_since, 1),
                "days_since_upload": days_since,
            })
    return all_details


def _parse_iso_duration(iso: str) -> int:
    """Parse ISO 8601 duration like PT1H23M45S → seconds."""
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def fetch_videos():
    """Fetch videos for all creators and categorize as best/mid/recent."""
    cfg = DEFAULT_CONFIG
    yt = _get_youtube_client()

    with get_db() as conn:
        creators = conn.execute(
            "SELECT * FROM creators WHERE channel_id IS NOT NULL ORDER BY niche, tier"
        ).fetchall()

        for c in creators:
            niche_cfg = cfg.niches.get(c["niche"])
            if not niche_cfg:
                continue

            n_best = niche_cfg.best_videos
            n_mid = niche_cfg.mid_videos
            n_recent = niche_cfg.recent_videos
            total_needed = niche_cfg.videos_per_creator

            print(f"\n{c['name']} ({c['niche']}) — fetching videos...")

            try:
                playlist_id = _get_uploads_playlist_id(yt, c["channel_id"])
                if not playlist_id:
                    print(f"  ✗ No uploads playlist found")
                    continue

                video_ids = _fetch_all_video_ids(yt, playlist_id, max_results=300)
                if not video_ids:
                    print(f"  ✗ No videos found")
                    continue

                details = _fetch_video_details(yt, video_ids)

                # Filter: only videos > 3 min (skip Shorts, intros)
                long_form = [d for d in details if d["duration_seconds"] >= 180]
                if len(long_form) < total_needed:
                    print(f"  ⚠ Only {len(long_form)} long-form videos (need {total_needed})")
                    long_form = details  # fall back to all

                # Sort by views_per_day for "best" (velocity, not raw views)
                by_velocity = sorted(long_form, key=lambda x: x["views_per_day"], reverse=True)

                # "best" = top by velocity
                best = by_velocity[:n_best]

                # "mid" = 40-60th percentile by velocity
                mid_start = len(by_velocity) * 4 // 10
                mid_end = len(by_velocity) * 6 // 10
                mid_pool = by_velocity[mid_start:mid_end]
                mid = mid_pool[:n_mid] if len(mid_pool) >= n_mid else by_velocity[n_best : n_best + n_mid]

                # "recent" = most recently published
                by_date = sorted(long_form, key=lambda x: x["published_at"], reverse=True)
                # Exclude videos already in best/mid
                used_ids = {v["video_id"] for v in best + mid}
                recent = [v for v in by_date if v["video_id"] not in used_ids][:n_recent]

                selected = (
                    [(v, "best") for v in best]
                    + [(v, "mid") for v in mid]
                    + [(v, "recent") for v in recent]
                )

                for v, category in selected:
                    insert_video(
                        conn,
                        video_id=v["video_id"],
                        creator_id=c["id"],
                        title=v["title"],
                        url=f"https://www.youtube.com/watch?v={v['video_id']}",
                        views=v["views"],
                        likes=v["likes"],
                        comments=v["comments"],
                        published_at=v["published_at"],
                        duration_seconds=v["duration_seconds"],
                        views_per_day=v["views_per_day"],
                        performance_category=category,
                        dataset_split="train",  # placeholder, assigned in split step
                        niche=c["niche"],
                        creator_name=c["name"],
                    )

                print(f"  ✓ {len(selected)} videos saved ({n_best} best, {len(mid)} mid, {len(recent)} recent)")

            except Exception as e:
                print(f"  ✗ Error: {e}")

    total = 0
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    print(f"\nTotal videos in DB: {total}")


# ── Step 4: Train/test split + review order ───────────────────────────

def assign_split():
    """80/20 train/test split maintaining niche + creator + category diversity."""
    cfg = DEFAULT_CONFIG
    random.seed(42)  # reproducible

    with get_db() as conn:
        videos = conn.execute(
            "SELECT id, video_id, niche, creator_name, performance_category FROM videos ORDER BY niche, creator_name"
        ).fetchall()

        # Group by (niche, creator)
        groups = defaultdict(list)
        for v in videos:
            groups[(v["niche"], v["creator_name"])].append(dict(v))

        train_ids = []
        test_ids = []

        for (niche, creator), vids in groups.items():
            random.shuffle(vids)
            n_train = max(1, round(len(vids) * cfg.train_ratio))
            train_ids.extend([v["video_id"] for v in vids[:n_train]])
            test_ids.extend([v["video_id"] for v in vids[n_train:]])

        # Assign splits
        for vid in train_ids:
            conn.execute("UPDATE videos SET dataset_split='train' WHERE video_id=?", (vid,))
        for vid in test_ids:
            conn.execute("UPDATE videos SET dataset_split='test' WHERE video_id=?", (vid,))

        # Compute diversified review order for training set
        train_videos = conn.execute(
            "SELECT video_id, niche, creator_name, performance_category FROM videos WHERE dataset_split='train' ORDER BY niche"
        ).fetchall()

        # Round-robin across niches, then across creators within each niche
        by_niche = defaultdict(list)
        for v in train_videos:
            by_niche[v["niche"]].append(dict(v))

        for niche in by_niche:
            by_creator = defaultdict(list)
            for v in by_niche[niche]:
                by_creator[v["creator_name"]].append(v)
            # Interleave creators
            interleaved = []
            creator_lists = [list(vids) for vids in by_creator.values()]
            for cl in creator_lists:
                random.shuffle(cl)
            max_len = max(len(cl) for cl in creator_lists)
            for i in range(max_len):
                for cl in creator_lists:
                    if i < len(cl):
                        interleaved.append(cl[i])
            by_niche[niche] = interleaved

        # Round-robin across niches
        ordered = []
        niche_names = sorted(by_niche.keys())
        max_niche_len = max(len(by_niche[n]) for n in niche_names)
        for i in range(max_niche_len):
            for niche in niche_names:
                if i < len(by_niche[niche]):
                    ordered.append(by_niche[niche][i])

        for idx, v in enumerate(ordered):
            conn.execute(
                "UPDATE videos SET review_order=? WHERE video_id=?",
                (idx, v["video_id"]),
            )

        print(f"Split: {len(train_ids)} train, {len(test_ids)} test")
        print(f"Review order assigned for {len(ordered)} training videos")

        # Print distribution
        for niche in niche_names:
            n_train = len([v for v in ordered if v["niche"] == niche])
            n_test = sum(1 for vid in test_ids if any(
                v["video_id"] == vid and v["niche"] == niche
                for v in [dict(r) for r in conn.execute(
                    "SELECT video_id, niche FROM videos WHERE video_id=?", (vid,)
                ).fetchall()]
            ))
            print(f"  {niche}: {n_train} train")


# ── Step 5: Export to Excel ───────────────────────────────────────────

def export_spreadsheet():
    """Export to Excel with Sheet 1 = train, Sheet 2 = test."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()

    headers = [
        "Video ID", "Creator Country", "Audience Country", "Content Language",
        "Niche", "Tier", "Creator Name", "Subscribers", "YouTube URL",
        "Title", "Views", "Likes", "Comments", "Views/Day",
        "Published", "Duration (min)", "Performance Category",
        "Transcript Path", "Review Order",
    ]
    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_text = Font(bold=True, color="FFFFFF")

    with get_db() as conn:
        for split, sheet_name in [("train", "Training (80%)"), ("test", "Test (20%)")]:
            ws = wb.active if split == "train" else wb.create_sheet()
            ws.title = sheet_name

            # Write headers
            for col, h in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=h)
                cell.font = header_text
                cell.fill = header_fill

            rows = conn.execute(
                """SELECT v.*, c.subscriber_count, c.tier, c.country,
                          c.audience_country, c.content_language
                   FROM videos v
                   JOIN creators c ON v.creator_id = c.id
                   WHERE v.dataset_split = ?
                   ORDER BY v.review_order""",
                (split,),
            ).fetchall()

            for row_idx, r in enumerate(rows, 2):
                vals = [
                    r["video_id"],
                    r["country"],
                    r["audience_country"],
                    r["content_language"],
                    r["niche"],
                    r["tier"],
                    r["creator_name"],
                    r["subscriber_count"],
                    r["url"],
                    r["title"],
                    r["views"],
                    r["likes"],
                    r["comments"],
                    r["views_per_day"],
                    r["published_at"],
                    round(r["duration_seconds"] / 60, 1) if r["duration_seconds"] else 0,
                    r["performance_category"],
                    r["transcript_path"] or "",
                    r["review_order"],
                ]
                for col, val in enumerate(vals, 1):
                    ws.cell(row=row_idx, column=col, value=val)

            # Auto-width columns
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(50, max_len + 2)

    out_path = EVAL_DIR / "hookcut_eval_dataset.xlsx"
    wb.save(str(out_path))
    print(f"Exported to {out_path}")


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    commands = {
        "seed": seed_creators,
        "enrich": enrich_creators,
        "fetch-videos": fetch_videos,
        "split": assign_split,
        "export": export_spreadsheet,
    }

    if cmd == "all":
        for step_name, fn in commands.items():
            print(f"\n{'='*60}")
            print(f"  STEP: {step_name}")
            print(f"{'='*60}")
            fn()
    elif cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
