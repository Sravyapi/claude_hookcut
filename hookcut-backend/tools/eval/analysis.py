#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis module - aggregates review data and generates failure mode dashboards.

Usage:
    python analysis.py <batch_number>         # Analyze a specific batch
    python analysis.py all                     # Analyze all reviewed data
    python analysis.py compare <v1> <v2>      # Compare two prompt versions
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from db import get_db


def analyze_batch(batch_number: int) -> dict:
    """Aggregate review data for a batch and return structured analysis."""
    with get_db() as conn:
        reviews = conn.execute(
            """SELECT r.*, h.hook_type, h.funnel_role, h.attention_score,
                      h.virality_score, h.duration_seconds, h.cognitive_tension,
                      h.scores, h.video_id,
                      v.niche, v.creator_name, v.performance_category
               FROM reviews r
               JOIN hooks h ON r.hook_id = h.id
               JOIN videos v ON h.video_id = v.video_id
               JOIN video_reviews vr ON h.video_id = vr.video_id
               WHERE vr.batch_number = ?""",
            (batch_number,),
        ).fetchall()

        missed = conn.execute(
            """SELECT mh.*, v.niche, v.creator_name
               FROM missed_hooks mh
               JOIN videos v ON mh.video_id = v.video_id
               JOIN video_reviews vr ON mh.video_id = vr.video_id
               WHERE vr.batch_number = ?""",
            (batch_number,),
        ).fetchall()

        video_reviews = conn.execute(
            "SELECT * FROM video_reviews WHERE batch_number=?", (batch_number,)
        ).fetchall()

    if not reviews:
        return {"error": f"No reviews found for batch {batch_number}"}

    total = len(reviews)

    # ── 1. Overall quality distribution ──
    rating_dist = Counter(r["rating"] for r in reviews)
    avg_rating = sum(r["rating"] for r in reviews) / total

    # ── 2. Boundary accuracy breakdown ──
    boundary_dist = Counter(r["boundary_accuracy"] for r in reviews)
    boundary_pct = {k: round(v / total * 100, 1) for k, v in boundary_dist.items()}

    # ── 3. Would-pick distribution ──
    pick_dist = Counter(r["would_pick"] for r in reviews)
    pick_pct = {k: round(v / total * 100, 1) for k, v in pick_dist.items()}

    # ── 4. Failure modes (hooks rated 1-2 or "would not pick") ──
    failures = [r for r in reviews if r["rating"] <= 2 or r["would_pick"] == "no"]
    failure_reasons = defaultdict(int)
    for f in failures:
        if f["boundary_accuracy"] == "wrong":
            failure_reasons["Wrong boundaries"] += 1
        elif f["boundary_accuracy"] == "slightly_off":
            failure_reasons["Boundary slightly off"] += 1
        if f["rating"] <= 2 and f["boundary_accuracy"] == "perfect":
            failure_reasons["Right moment, low quality hook"] += 1
        if f["would_pick"] == "no" and f["rating"] >= 3:
            failure_reasons["Decent quality but not top 5 material"] += 1

    failure_pct = {k: round(v / max(1, len(failures)) * 100, 1) for k, v in failure_reasons.items()}

    # ── 5. By niche ──
    niche_stats = defaultdict(lambda: {"total": 0, "avg_rating": 0, "ratings": [],
                                        "would_pick_yes": 0, "boundary_perfect": 0})
    for r in reviews:
        n = r["niche"]
        niche_stats[n]["total"] += 1
        niche_stats[n]["ratings"].append(r["rating"])
        if r["would_pick"] == "yes":
            niche_stats[n]["would_pick_yes"] += 1
        if r["boundary_accuracy"] == "perfect":
            niche_stats[n]["boundary_perfect"] += 1

    for n in niche_stats:
        s = niche_stats[n]
        s["avg_rating"] = round(sum(s["ratings"]) / s["total"], 2)
        s["pick_rate"] = round(s["would_pick_yes"] / s["total"] * 100, 1)
        s["boundary_accuracy_pct"] = round(s["boundary_perfect"] / s["total"] * 100, 1)
        del s["ratings"]

    # ── 6. By hook type ──
    type_stats = defaultdict(lambda: {"total": 0, "avg_rating": 0, "ratings": [], "would_pick_yes": 0})
    for r in reviews:
        ht = r["hook_type"]
        type_stats[ht]["total"] += 1
        type_stats[ht]["ratings"].append(r["rating"])
        if r["would_pick"] == "yes":
            type_stats[ht]["would_pick_yes"] += 1

    for ht in type_stats:
        s = type_stats[ht]
        s["avg_rating"] = round(sum(s["ratings"]) / s["total"], 2)
        s["pick_rate"] = round(s["would_pick_yes"] / s["total"] * 100, 1)
        del s["ratings"]

    # ── 7. LLM score vs human rating correlation ──
    score_vs_rating = []
    for r in reviews:
        score_vs_rating.append({
            "attention_score": r["attention_score"],
            "virality_score": r["virality_score"],
            "human_rating": r["rating"],
            "would_pick": r["would_pick"],
        })

    # Simple correlation: avg LLM attention_score for each human rating level
    llm_by_human_rating = defaultdict(list)
    for s in score_vs_rating:
        llm_by_human_rating[s["human_rating"]].append(s["attention_score"])
    llm_calibration = {
        k: round(sum(v) / len(v), 2)
        for k, v in sorted(llm_by_human_rating.items())
    }

    # ── 8. Missed hooks ──
    missed_count = len(missed)
    missed_by_niche = Counter(m["niche"] for m in missed)

    # ── 9. Performance category analysis ──
    cat_stats = defaultdict(lambda: {"total": 0, "avg_rating": 0, "ratings": []})
    for r in reviews:
        cat = r["performance_category"]
        cat_stats[cat]["total"] += 1
        cat_stats[cat]["ratings"].append(r["rating"])
    for cat in cat_stats:
        s = cat_stats[cat]
        s["avg_rating"] = round(sum(s["ratings"]) / s["total"], 2)
        del s["ratings"]

    return {
        "batch_number": batch_number,
        "total_hooks_reviewed": total,
        "total_videos_reviewed": len(video_reviews),
        "avg_rating": round(avg_rating, 2),
        "rating_distribution": dict(rating_dist),
        "boundary_accuracy": boundary_pct,
        "would_pick": pick_pct,
        "failure_modes": failure_pct,
        "failure_count": len(failures),
        "by_niche": dict(niche_stats),
        "by_hook_type": dict(type_stats),
        "llm_score_calibration": llm_calibration,
        "missed_hooks_count": missed_count,
        "missed_hooks_by_niche": dict(missed_by_niche),
        "by_performance_category": dict(cat_stats),
    }


def compare_versions(v1: str, v2: str) -> dict:
    """Compare review metrics between two prompt versions."""
    with get_db() as conn:
        def _version_stats(version):
            rows = conn.execute(
                """SELECT r.rating, r.boundary_accuracy, r.would_pick,
                          h.attention_score, h.hook_type, v.niche
                   FROM reviews r
                   JOIN hooks h ON r.hook_id = h.id
                   JOIN videos v ON h.video_id = v.video_id
                   WHERE h.prompt_version = ?""",
                (version,),
            ).fetchall()
            if not rows:
                return None
            total = len(rows)
            return {
                "version": version,
                "total_reviews": total,
                "avg_rating": round(sum(r["rating"] for r in rows) / total, 2),
                "would_pick_yes_pct": round(
                    sum(1 for r in rows if r["would_pick"] == "yes") / total * 100, 1
                ),
                "boundary_perfect_pct": round(
                    sum(1 for r in rows if r["boundary_accuracy"] == "perfect") / total * 100, 1
                ),
                "avg_llm_attention": round(
                    sum(r["attention_score"] for r in rows) / total, 2
                ),
            }

        s1 = _version_stats(v1)
        s2 = _version_stats(v2)

    if not s1 or not s2:
        return {"error": "One or both versions have no review data"}

    return {
        "v1": s1,
        "v2": s2,
        "improvement": {
            "avg_rating_delta": round(s2["avg_rating"] - s1["avg_rating"], 2),
            "pick_rate_delta": round(s2["would_pick_yes_pct"] - s1["would_pick_yes_pct"], 1),
            "boundary_delta": round(s2["boundary_perfect_pct"] - s1["boundary_perfect_pct"], 1),
        },
    }


def print_analysis(analysis: dict):
    """Pretty-print analysis results."""
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        return

    print(f"\n{'='*60}")
    print(f"  BATCH {analysis['batch_number']} ANALYSIS")
    print(f"{'='*60}")
    print(f"  Videos reviewed: {analysis['total_videos_reviewed']}")
    print(f"  Hooks reviewed:  {analysis['total_hooks_reviewed']}")
    print(f"  Average rating:  {analysis['avg_rating']} / 5")
    print()

    print("  RATING DISTRIBUTION:")
    for rating in range(1, 6):
        count = analysis['rating_distribution'].get(rating, 0)
        bar = "█" * count
        print(f"    {rating}★: {bar} ({count})")

    print(f"\n  BOUNDARY ACCURACY:")
    for k, v in analysis["boundary_accuracy"].items():
        print(f"    {k}: {v}%")

    print(f"\n  WOULD PICK:")
    for k, v in analysis["would_pick"].items():
        print(f"    {k}: {v}%")

    print(f"\n  FAILURE MODES ({analysis['failure_count']} failures):")
    for k, v in sorted(analysis["failure_modes"].items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}%")

    print(f"\n  LLM SCORE CALIBRATION (avg LLM attention_score per human rating):")
    for human, llm in analysis["llm_score_calibration"].items():
        print(f"    Human {human}★ → LLM {llm}/10")

    print(f"\n  BY NICHE:")
    for niche, stats in sorted(analysis["by_niche"].items()):
        print(f"    {niche}: avg {stats['avg_rating']}★, pick {stats['pick_rate']}%, "
              f"boundary perfect {stats['boundary_accuracy_pct']}%")

    print(f"\n  BY HOOK TYPE:")
    for ht, stats in sorted(analysis["by_hook_type"].items(), key=lambda x: -x[1]["avg_rating"]):
        print(f"    {ht}: avg {stats['avg_rating']}★, pick {stats['pick_rate']}% (n={stats['total']})")

    print(f"\n  MISSED HOOKS: {analysis['missed_hooks_count']}")
    if analysis["missed_hooks_by_niche"]:
        for niche, count in analysis["missed_hooks_by_niche"].items():
            print(f"    {niche}: {count}")

    print(f"\n  BY PERFORMANCE CATEGORY:")
    for cat, stats in analysis["by_performance_category"].items():
        print(f"    {cat}: avg {stats['avg_rating']}★ (n={stats['total']})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "all":
        with get_db() as conn:
            batches = conn.execute("SELECT DISTINCT batch_number FROM video_reviews ORDER BY batch_number").fetchall()
        for b in batches:
            result = analyze_batch(b["batch_number"])
            print_analysis(result)
    elif sys.argv[1] == "compare" and len(sys.argv) >= 4:
        result = compare_versions(sys.argv[2], sys.argv[3])
        print(json.dumps(result, indent=2))
    else:
        result = analyze_batch(int(sys.argv[1]))
        print_analysis(result)
