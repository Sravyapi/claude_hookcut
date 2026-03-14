# -*- coding: utf-8 -*-
"""SQLite database - single source of truth for the eval framework."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS creators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT UNIQUE,
    handle TEXT,
    name TEXT NOT NULL,
    subscriber_count INTEGER,
    country TEXT DEFAULT 'India',
    audience_country TEXT DEFAULT 'India',
    content_language TEXT DEFAULT 'English',
    niche TEXT NOT NULL,
    tier INTEGER NOT NULL,
    channel_url TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    creator_id INTEGER REFERENCES creators(id),
    title TEXT,
    url TEXT NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    published_at TEXT,
    duration_seconds INTEGER DEFAULT 0,
    views_per_day REAL DEFAULT 0,
    performance_category TEXT NOT NULL CHECK(performance_category IN ('best','mid','recent')),
    dataset_split TEXT NOT NULL CHECK(dataset_split IN ('train','test')),
    review_order INTEGER,
    niche TEXT NOT NULL,
    creator_name TEXT,
    transcript_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE REFERENCES videos(video_id),
    text TEXT,
    provider TEXT,
    char_count INTEGER DEFAULT 0,
    file_path TEXT,
    fetched_at TEXT DEFAULT (datetime('now')),
    error TEXT
);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    description TEXT,
    prompt_hash TEXT,
    prompt_snapshot TEXT,
    parent_version TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT REFERENCES videos(video_id),
    prompt_version TEXT REFERENCES prompt_versions(version),
    rank INTEGER,
    hook_text TEXT,
    start_time TEXT,
    end_time TEXT,
    start_seconds REAL,
    end_seconds REAL,
    duration_seconds REAL,
    hook_type TEXT,
    funnel_role TEXT,
    cognitive_tension TEXT,
    scores TEXT,
    attention_score REAL,
    virality_score REAL,
    justification TEXT,
    algorithm_dynamics TEXT,
    viewer_psychology TEXT,
    improvement_suggestion TEXT,
    is_composite INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(video_id, prompt_version, rank)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hook_id INTEGER REFERENCES hooks(id),
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    boundary_accuracy TEXT CHECK(boundary_accuracy IN ('perfect','slightly_off','wrong')),
    would_pick TEXT CHECK(would_pick IN ('yes','maybe','no')),
    justification TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS missed_hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT REFERENCES videos(video_id),
    prompt_version TEXT,
    timestamp_range TEXT,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS video_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT REFERENCES videos(video_id),
    prompt_version TEXT,
    overall_feedback TEXT,
    batch_number INTEGER,
    reviewed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS review_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_number INTEGER UNIQUE,
    prompt_version TEXT,
    videos_target INTEGER,
    videos_completed INTEGER DEFAULT 0,
    started_at TEXT,
    completed_at TEXT,
    analysis_summary TEXT
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


@contextmanager
def get_db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- CRUD helpers ---

def insert_creator(conn, *, name, niche, tier, handle=None, channel_id=None,
                   subscriber_count=None, country="India", audience_country="India",
                   content_language="English", channel_url=None):
    conn.execute(
        """INSERT OR IGNORE INTO creators
           (name, niche, tier, handle, channel_id, subscriber_count, country,
            audience_country, content_language, channel_url)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (name, niche, tier, handle, channel_id, subscriber_count, country,
         audience_country, content_language, channel_url),
    )


def insert_video(conn, *, video_id, creator_id, title, url, views, likes, comments,
                 published_at, duration_seconds, views_per_day, performance_category,
                 dataset_split, niche, creator_name, review_order=None,
                 content_language="English"):
    conn.execute(
        """INSERT OR IGNORE INTO videos
           (video_id, creator_id, title, url, views, likes, comments, published_at,
            duration_seconds, views_per_day, performance_category, dataset_split,
            niche, creator_name, review_order, content_language)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (video_id, creator_id, title, url, views, likes, comments, published_at,
         duration_seconds, views_per_day, performance_category, dataset_split,
         niche, creator_name, review_order, content_language),
    )


def insert_transcript(conn, *, video_id, text, provider, file_path, error=None):
    char_count = len(text) if text else 0
    conn.execute(
        """INSERT OR REPLACE INTO transcripts
           (video_id, text, provider, char_count, file_path, error)
           VALUES (?,?,?,?,?,?)""",
        (video_id, text, provider, char_count, file_path, error),
    )


def insert_prompt_version(conn, *, version, description, prompt_hash, prompt_snapshot,
                          parent_version=None):
    conn.execute(
        """INSERT OR IGNORE INTO prompt_versions
           (version, description, prompt_hash, prompt_snapshot, parent_version)
           VALUES (?,?,?,?,?)""",
        (version, description, prompt_hash, prompt_snapshot, parent_version),
    )


def insert_hook(conn, *, video_id, prompt_version, rank, hook_text, start_time,
                end_time, start_seconds, end_seconds, duration_seconds, hook_type,
                funnel_role, cognitive_tension, scores, attention_score, virality_score,
                justification, algorithm_dynamics, viewer_psychology,
                improvement_suggestion, is_composite):
    conn.execute(
        """INSERT OR REPLACE INTO hooks
           (video_id, prompt_version, rank, hook_text, start_time, end_time,
            start_seconds, end_seconds, duration_seconds, hook_type, funnel_role,
            cognitive_tension, scores, attention_score, virality_score, justification,
            algorithm_dynamics, viewer_psychology, improvement_suggestion, is_composite)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (video_id, prompt_version, rank, hook_text, start_time, end_time,
         start_seconds, end_seconds, duration_seconds, hook_type, funnel_role,
         cognitive_tension, json.dumps(scores) if isinstance(scores, dict) else scores,
         attention_score, virality_score, justification,
         json.dumps(algorithm_dynamics) if isinstance(algorithm_dynamics, dict) else algorithm_dynamics,
         json.dumps(viewer_psychology) if isinstance(viewer_psychology, dict) else viewer_psychology,
         improvement_suggestion, int(is_composite)),
    )


def insert_review(conn, *, hook_id, rating, boundary_accuracy, would_pick, justification):
    conn.execute(
        """INSERT INTO reviews (hook_id, rating, boundary_accuracy, would_pick, justification)
           VALUES (?,?,?,?,?)""",
        (hook_id, rating, boundary_accuracy, would_pick, justification),
    )


def insert_missed_hook(conn, *, video_id, prompt_version, timestamp_range, description):
    conn.execute(
        """INSERT INTO missed_hooks (video_id, prompt_version, timestamp_range, description)
           VALUES (?,?,?,?)""",
        (video_id, prompt_version, timestamp_range, description),
    )


def insert_video_review(conn, *, video_id, prompt_version, overall_feedback, batch_number):
    conn.execute(
        """INSERT INTO video_reviews (video_id, prompt_version, overall_feedback, batch_number)
           VALUES (?,?,?,?)""",
        (video_id, prompt_version, overall_feedback, batch_number),
    )


def get_review_progress(conn) -> dict:
    """Return overall review progress stats."""
    total = conn.execute("SELECT COUNT(*) FROM videos WHERE dataset_split='train'").fetchone()[0]
    reviewed = conn.execute(
        "SELECT COUNT(DISTINCT video_id) FROM video_reviews"
    ).fetchone()[0]
    by_niche = conn.execute(
        """SELECT v.niche,
                  COUNT(*) as total,
                  COUNT(vr.id) as reviewed
           FROM videos v
           LEFT JOIN video_reviews vr ON v.video_id = vr.video_id
           WHERE v.dataset_split = 'train'
           GROUP BY v.niche"""
    ).fetchall()
    return {
        "total": total,
        "reviewed": reviewed,
        "pct": round(reviewed / total * 100, 1) if total else 0,
        "by_niche": [dict(r) for r in by_niche],
    }


def get_next_video_to_review(conn, prompt_version: str) -> dict | None:
    """Get the next unreviewed training video that has hooks ready, in diversified order."""
    row = conn.execute(
        """SELECT v.* FROM videos v
           WHERE v.dataset_split = 'train'
             AND v.video_id NOT IN (SELECT video_id FROM video_reviews WHERE prompt_version = ?)
             AND v.video_id IN (SELECT video_id FROM hooks WHERE prompt_version = ?)
           ORDER BY v.review_order ASC
           LIMIT 1""",
        (prompt_version, prompt_version),
    ).fetchone()
    return dict(row) if row else None


def get_hooks_for_video(conn, video_id: str, prompt_version: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM hooks WHERE video_id=? AND prompt_version=? ORDER BY rank",
        (video_id, prompt_version),
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_reviews_for_batch(conn, batch_number: int) -> list[dict]:
    rows = conn.execute(
        """SELECT r.*, h.hook_type, h.funnel_role, h.attention_score, h.virality_score,
                  h.video_id, h.start_seconds, h.end_seconds, h.duration_seconds,
                  v.niche, v.creator_name, v.performance_category
           FROM reviews r
           JOIN hooks h ON r.hook_id = h.id
           JOIN videos v ON h.video_id = v.video_id
           JOIN video_reviews vr ON h.video_id = vr.video_id
           WHERE vr.batch_number = ?""",
        (batch_number,),
    ).fetchall()
    return [dict(r) for r in rows]


init_db()
