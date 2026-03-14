#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HookCut Eval Framework - Streamlit Review UI v2

Features:
  - Paste-based hook import (copy transcript → paste into Gemini Gem → paste JSON back)
  - Dual-model comparison (3.1 Pro vs 2.5 Flash side-by-side)
  - Diversified batch review (10% at a time across all niches)
  - Rich analytics with model comparison charts

Run: streamlit run tools/eval/app.py
"""

import json
import math
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import (
    get_db, get_review_progress, get_next_video_to_review,
    get_hooks_for_video, insert_review, insert_missed_hook,
    insert_video_review, insert_hook, insert_prompt_version,
)
from analysis import analyze_batch, compare_versions
from config import DEFAULT_CONFIG, BATCH_SIZE_PCT

EVAL_DIR = Path(__file__).resolve().parent

# ── Models ────────────────────────────────────────────────────────
MODELS = {
    "v1-pro": {"label": "Gemini 3.1 Pro", "short": "Pro", "color": "#7c3aed", "bg": "#ede9fe"},
    "v1-flash": {"label": "Gemini 2.5 Flash", "short": "Flash", "color": "#0891b2", "bg": "#e0f2fe"},
}
MODEL_VERSIONS = list(MODELS.keys())

# ── Theme & Config ────────────────────────────────────────────────

st.set_page_config(
    page_title="HookCut Eval",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Restore state from URL query params (survives browser refresh)
_qp = st.query_params
if "vid" in _qp and "review_video_id" not in st.session_state:
    st.session_state["review_video_id"] = _qp["vid"]
    st.session_state["review_mode"] = _qp.get("mode", "review")
    st.session_state["nav_to_review"] = True
if "page" in _qp and "page_override" not in st.session_state:
    st.session_state["page_override"] = _qp["page"]

# ── CSS ───────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Layout */
    .block-container { padding-top: 1rem; max-width: 1400px; }
    [data-testid="stSidebar"] { background: #0f172a; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio label { color: #94a3b8 !important; font-size: 0.8rem; }

    /* Niche pills */
    .niche-pill {
        display: inline-block; padding: 3px 12px; border-radius: 999px;
        font-size: 0.7rem; font-weight: 700; color: white; letter-spacing: 0.02em;
    }
    .niche-finance { background: #2563eb; }
    .niche-tech { background: #7c3aed; }
    .niche-entrepreneurship { background: #059669; }
    .niche-education { background: #d97706; }
    .niche-podcast { background: #dc2626; }
    .niche-fitness { background: #0891b2; }
    .niche-drama { background: #be185d; }

    /* Status badges */
    .badge {
        display: inline-block; padding: 2px 10px; border-radius: 4px;
        font-size: 0.7rem; font-weight: 700; letter-spacing: 0.03em;
    }
    .badge-ready { background: #dbeafe; color: #1e40af; }
    .badge-reviewed { background: #dcfce7; color: #166534; }
    .badge-needs-hooks { background: #fef3c7; color: #92400e; }
    .badge-no-transcript { background: #fee2e2; color: #991b1b; }
    .badge-partial { background: #e9d5ff; color: #6b21a8; }

    /* Model badges */
    .model-badge {
        display: inline-block; padding: 3px 10px; border-radius: 4px;
        font-size: 0.72rem; font-weight: 700;
    }
    .model-pro { background: #ede9fe; color: #7c3aed; }
    .model-flash { background: #e0f2fe; color: #0891b2; }

    /* Score bars */
    .score-bar-wrap { margin-bottom: 2px; }
    .score-bar-label { font-size: 0.65rem; color: #64748b; margin-bottom: 1px; }
    .score-bar-outer {
        height: 5px; border-radius: 3px; background: #e2e8f0; overflow: hidden;
    }
    .score-bar-fill {
        height: 100%; border-radius: 3px; transition: width 0.3s;
    }
    .score-bar-val { font-size: 0.75rem; font-weight: 600; color: #1e293b; }

    /* Hook card */
    .hook-card {
        border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 16px 20px; margin-bottom: 12px;
        background: #fafbfc; transition: border-color 0.2s, box-shadow 0.2s;
    }
    .hook-card:hover { border-color: #93c5fd; box-shadow: 0 2px 8px rgba(59,130,246,0.08); }

    /* Video row */
    .video-row {
        border-bottom: 1px solid #f1f5f9; padding: 10px 0;
        transition: background 0.15s;
    }
    .video-row:hover { background: #f8fafc; }

    /* Star display */
    .stars { color: #f59e0b; font-size: 1.1rem; letter-spacing: 1px; }

    /* Transcript box */
    .transcript-box {
        background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 16px; font-family: monospace; font-size: 0.82rem;
        max-height: 300px; overflow-y: auto; line-height: 1.6;
        white-space: pre-wrap; color: #334155;
    }

    /* Section headers */
    .section-title {
        font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.08em; color: #64748b; margin-bottom: 8px;
    }

    /* Metrics card */
    .metric-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 16px; text-align: center;
    }
    .metric-value { font-size: 1.8rem; font-weight: 800; color: #0f172a; }
    .metric-label { font-size: 0.72rem; color: #64748b; font-weight: 600; text-transform: uppercase; }

    /* YouTube link pill */
    .yt-link {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 2px 8px; border-radius: 4px; text-decoration: none;
        font-size: 0.72rem; font-weight: 600;
        background: #fee2e2; color: #b91c1c;
        transition: background 0.15s;
    }
    .yt-link:hover { background: #fca5a5; color: #7f1d1d; }

    /* Transcript path */
    .transcript-path {
        font-family: monospace; font-size: 0.7rem; color: #16a34a;
        word-break: break-all; line-height: 1.4;
    }
    .transcript-path-missing { font-size: 0.7rem; color: #94a3b8; }

    /* Action link button */
    .action-link {
        display: inline-block; padding: 3px 10px; border-radius: 5px;
        border: 1px solid #e2e8f0; text-decoration: none;
        font-size: 0.75rem; font-weight: 600; color: #475569;
        background: white; cursor: pointer;
    }
    .action-link:hover { background: #f1f5f9; border-color: #cbd5e1; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────

NICHE_CSS = {
    "Finance": "finance", "Tech / AI": "tech", "Entrepreneurship": "entrepreneurship",
    "Education": "education", "Podcast": "podcast", "Fitness": "fitness",
    "Drama / Commentary": "drama",
}

NICHE_SHORT = {
    "Entrepreneurship": "Entrepr.",
    "Drama / Commentary": "Drama",
    "Tech / AI": "Tech/AI",
    "Education": "Edu",
    "Fitness": "Fit",
    "Finance": "Finance",
    "Podcast": "Podcast",
}

def niche_pill(niche):
    css = NICHE_CSS.get(niche, "finance")
    label = NICHE_SHORT.get(niche, niche)
    return f'<span class="niche-pill niche-{css}">{label}</span>'

def model_badge(version):
    m = MODELS.get(version, {})
    css = "pro" if "pro" in version else "flash"
    return f'<span class="model-badge model-{css}">{m.get("label", version)}</span>'

def format_views(n):
    if not n: return "0"
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def format_duration(s):
    if not s: return "0:00"
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"

def stars_html(rating):
    full = int(rating)
    return f'<span class="stars">{"★" * full}{"☆" * (5 - full)}</span> <span style="font-size:0.85rem;color:#475569;">{rating:.1f}</span>'

def score_bar(label, val, max_val=10):
    pct = min(100, (val / max_val) * 100) if val else 0
    color = "#ef4444" if pct < 40 else "#f59e0b" if pct < 65 else "#22c55e"
    return (
        f'<div class="score-bar-wrap">'
        f'<div style="display:flex;justify-content:space-between;">'
        f'<span class="score-bar-label">{label}</span>'
        f'<span class="score-bar-val">{val}</span></div>'
        f'<div class="score-bar-outer"><div class="score-bar-fill" style="width:{pct}%;background:{color};"></div></div>'
        f'</div>'
    )


def render_copy_button(text: str, label: str = "📋 Copy", key: str = "", height: int = 42):
    """Render a clipboard copy button. Uses execCommand fallback for Streamlit iframes."""
    escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    components.html(f"""
    <textarea id="copyta_{key}" style="position:absolute;left:-9999px;top:-9999px;"
        readonly>{escaped}</textarea>
    <button id="copybtn_{key}" onclick="
        var ta = document.getElementById('copyta_{key}');
        ta.style.position = 'fixed';
        ta.style.left = '0';
        ta.style.top = '0';
        ta.select();
        ta.setSelectionRange(0, 999999);
        var ok = document.execCommand('copy');
        ta.style.position = 'absolute';
        ta.style.left = '-9999px';
        var btn = document.getElementById('copybtn_{key}');
        if (ok) {{
            btn.innerHTML = '✓ Copied!';
            btn.style.background = '#dcfce7';
            btn.style.borderColor = '#16a34a';
            btn.style.color = '#166534';
        }} else {{
            btn.innerHTML = '⚠ Select text below — Ctrl+A, Ctrl+C';
            btn.style.background = '#fef3c7';
        }}
        setTimeout(function() {{
            btn.innerHTML = '{label}';
            btn.style.background = '';
            btn.style.borderColor = '';
            btn.style.color = '';
        }}, 2500);
    " style="width:100%;padding:7px 14px;border-radius:7px;border:1px solid #cbd5e1;
        background:white;cursor:pointer;font-size:0.88rem;color:#1e293b;
        font-weight:600;transition:all 0.15s;font-family:system-ui,sans-serif;">
        {label}
    </button>
    """, height=height)


def get_video_status(v, version):
    """Return status considering a specific prompt version."""
    has_pro = False
    has_flash = False
    reviewed_pro = False
    reviewed_flash = False

    with get_db() as conn:
        for mv in MODEL_VERSIONS:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM hooks WHERE video_id=? AND prompt_version=?",
                (v["video_id"], mv),
            ).fetchone()[0]
            rev = conn.execute(
                "SELECT COUNT(*) FROM video_reviews WHERE video_id=? AND prompt_version=?",
                (v["video_id"], mv),
            ).fetchone()[0]
            if mv == "v1-pro":
                has_pro = cnt > 0
                reviewed_pro = rev > 0
            else:
                has_flash = cnt > 0
                reviewed_flash = rev > 0

    if reviewed_pro and reviewed_flash:
        return "both-reviewed", "Reviewed (Both)"
    if reviewed_pro or reviewed_flash:
        which = "Pro" if reviewed_pro else "Flash"
        return "partial", f"Reviewed ({which})"
    if has_pro and has_flash:
        return "ready", "Ready (Both)"
    if has_pro or has_flash:
        which = "Pro" if has_pro else "Flash"
        return "ready", f"Ready ({which})"
    if not v.get("has_transcript"):
        return "no-transcript", "No Transcript"
    return "needs-hooks", "Needs Hooks"

def status_badge_html(status_key, label):
    css_map = {
        "both-reviewed": "badge-reviewed",
        "partial": "badge-partial",
        "ready": "badge-ready",
        "needs-hooks": "badge-needs-hooks",
        "no-transcript": "badge-no-transcript",
    }
    return f'<span class="badge {css_map.get(status_key, "badge-needs-hooks")}">{label}</span>'


# ── Data Loading ──────────────────────────────────────────────────

def load_pipeline_stats():
    with get_db() as conn:
        total_videos = conn.execute(
            "SELECT COUNT(*) FROM videos WHERE dataset_split='train' AND COALESCE(content_language,'English')='English'"
        ).fetchone()[0]
        transcripts_done = conn.execute(
            """SELECT COUNT(*) FROM transcripts t
               JOIN videos v ON t.video_id=v.video_id
               WHERE t.text IS NOT NULL
                 AND v.dataset_split='train'
                 AND COALESCE(v.content_language,'English')='English'"""
        ).fetchone()[0]
        hooks_pro = conn.execute(
            """SELECT COUNT(DISTINCT h.video_id) FROM hooks h
               JOIN videos v ON h.video_id=v.video_id
               WHERE h.prompt_version='v1-pro' AND COALESCE(v.content_language,'English')='English'"""
        ).fetchone()[0]
        hooks_flash = conn.execute(
            """SELECT COUNT(DISTINCT h.video_id) FROM hooks h
               JOIN videos v ON h.video_id=v.video_id
               WHERE h.prompt_version='v1-flash' AND COALESCE(v.content_language,'English')='English'"""
        ).fetchone()[0]
        reviewed_pro = conn.execute(
            """SELECT COUNT(DISTINCT vr.video_id) FROM video_reviews vr
               JOIN videos v ON vr.video_id=v.video_id
               WHERE vr.prompt_version='v1-pro' AND COALESCE(v.content_language,'English')='English'"""
        ).fetchone()[0]
        reviewed_flash = conn.execute(
            """SELECT COUNT(DISTINCT vr.video_id) FROM video_reviews vr
               JOIN videos v ON vr.video_id=v.video_id
               WHERE vr.prompt_version='v1-flash' AND COALESCE(v.content_language,'English')='English'"""
        ).fetchone()[0]
    return {
        "total": total_videos, "transcripts": transcripts_done,
        "hooks_pro": hooks_pro, "hooks_flash": hooks_flash,
        "reviewed_pro": reviewed_pro, "reviewed_flash": reviewed_flash,
    }


def load_all_videos(prompt_version: str):
    """Load all English train videos with hook/review status for the given prompt version.
    Hindi-tagged videos are preserved in the DB but excluded from the eval UI.
    """
    with get_db() as conn:
        rows = conn.execute(
            """SELECT v.video_id, v.title, v.url, v.niche, v.creator_name,
                      v.views, v.likes, v.views_per_day, v.duration_seconds,
                      v.performance_category, v.dataset_split, v.review_order,
                      v.content_language,
                      COALESCE(t.file_path, v.transcript_path) as transcript_path,
                      CASE WHEN t.text IS NOT NULL THEN 1 ELSE 0 END as has_transcript,
                      CASE WHEN h.hook_count > 0 THEN 1 ELSE 0 END as has_hooks,
                      CASE WHEN vr.id IS NOT NULL THEN 1 ELSE 0 END as is_reviewed
               FROM videos v
               LEFT JOIN transcripts t ON v.video_id = t.video_id
               LEFT JOIN (SELECT video_id, COUNT(*) as hook_count FROM hooks
                          WHERE prompt_version = ? GROUP BY video_id) h
                   ON v.video_id = h.video_id
               LEFT JOIN video_reviews vr ON v.video_id = vr.video_id
                   AND vr.prompt_version = ?
               WHERE v.dataset_split = 'train'
                 AND COALESCE(v.content_language, 'English') = 'English'
               ORDER BY v.review_order""",
            (prompt_version, prompt_version),
        ).fetchall()
    return [dict(r) for r in rows]


def get_batch_info():
    """Return (batch_size, total_batches) computed from English train set size."""
    with get_db() as conn:
        train_count = conn.execute(
            "SELECT COUNT(*) FROM videos WHERE dataset_split='train' AND COALESCE(content_language,'English')='English'"
        ).fetchone()[0]
    batch_size = max(1, math.ceil(train_count * BATCH_SIZE_PCT / 100))
    total_batches = math.ceil(train_count / batch_size)
    return batch_size, total_batches


def load_batch_videos(prompt_version: str, batch_num: int | None = None):
    """Load videos for a specific batch number (1-based). If None, uses the current active batch."""
    videos = load_all_videos(prompt_version)
    batch_size, total_batches = get_batch_info()

    if batch_num is None:
        reviewed_count = sum(1 for v in videos if v["is_reviewed"])
        batch_num = min((reviewed_count // batch_size) + 1, total_batches)

    batch_start = (batch_num - 1) * batch_size
    batch_end = min(batch_start + batch_size, len(videos))
    batch_videos = videos[batch_start:batch_end]

    return {
        "all": videos,
        "batch": batch_videos,
        "batch_num": batch_num,
        "total_batches": total_batches,
        "batch_size": batch_size,
        "reviewed_count": sum(1 for v in batch_videos if v["is_reviewed"]),
    }


def ensure_model_versions():
    """Register both model versions if not present."""
    with get_db() as conn:
        for ver, info in MODELS.items():
            existing = conn.execute("SELECT version FROM prompt_versions WHERE version=?", (ver,)).fetchone()
            if not existing:
                import hashlib
                from app.llm.prompts.hook_identification import build_hook_prompt
                prompt_text = build_hook_prompt("Generic", "[PLACEHOLDER]", "English")
                prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()[:16]
                insert_prompt_version(
                    conn, version=ver,
                    description=f"{info['label']} — manual paste evaluation",
                    prompt_hash=prompt_hash, prompt_snapshot=prompt_text,
                )


def parse_hooks_json(raw_json: str) -> list[dict]:
    """Parse the JSON blob from Gemini and extract hooks list."""
    text = raw_json.strip()
    # Strip markdown fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    data = json.loads(text)

    # Handle both {"hooks": [...]} and bare [...]
    hooks = data if isinstance(data, list) else data.get("hooks", [])

    if not hooks:
        raise ValueError("No hooks found in JSON. Expected {\"hooks\": [...]} or [...]")
    if len(hooks) != 5:
        raise ValueError(f"Expected exactly 5 hooks, got {len(hooks)}")

    return hooks


def save_pasted_hooks(video_id: str, prompt_version: str, hooks: list[dict]):
    """Save parsed hooks to the database."""
    with get_db() as conn:
        for h in hooks:
            scores = h.get("scores", {})
            insert_hook(
                conn,
                video_id=video_id,
                prompt_version=prompt_version,
                rank=h.get("rank", 0),
                hook_text=h.get("hook_text", ""),
                start_time=h.get("start_time", "0:00"),
                end_time=h.get("end_time", "0:00"),
                start_seconds=_time_to_seconds(h.get("start_time", "0:00")),
                end_seconds=_time_to_seconds(h.get("end_time", "0:00")),
                duration_seconds=_time_to_seconds(h.get("end_time", "0:00")) - _time_to_seconds(h.get("start_time", "0:00")),
                hook_type=h.get("hook_type", "Unknown"),
                funnel_role=h.get("funnel_role", "unknown"),
                cognitive_tension=h.get("cognitive_tension", "unknown"),
                scores=scores,
                attention_score=h.get("attention_score", 0),
                virality_score=h.get("virality_score", 0),
                justification=h.get("justification", ""),
                algorithm_dynamics=h.get("algorithm_dynamics", {}),
                viewer_psychology=h.get("viewer_psychology", {}),
                improvement_suggestion=h.get("improvement_suggestion", ""),
                is_composite=h.get("is_composite", False),
            )


def _time_to_seconds(t: str) -> float:
    """Convert M:SS or H:MM:SS to seconds."""
    if not t or t == "0:00":
        return 0.0
    parts = t.replace("(inferred)", "").strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except (ValueError, IndexError):
        return 0.0


# Initialize model versions
try:
    ensure_model_versions()
except Exception:
    pass  # Will work once backend is importable


# ── Sidebar ───────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### HookCut Eval")
    st.caption(DEFAULT_CONFIG.name)

    st.divider()

    # Active model selector — default to v1-pro, persist in URL query param
    _qm = st.query_params.get("model", "v1-pro")
    _model_default_idx = MODEL_VERSIONS.index(_qm) if _qm in MODEL_VERSIONS else 0
    st.markdown('<div class="section-title">Active Model</div>', unsafe_allow_html=True)
    active_model = st.radio(
        "Model", MODEL_VERSIONS,
        index=_model_default_idx,
        format_func=lambda x: MODELS[x]["label"],
        label_visibility="collapsed",
        horizontal=True,
        key="active_model_radio",
    )
    st.query_params["model"] = active_model

    st.divider()

    # Pipeline stats
    stats = load_pipeline_stats()
    st.markdown('<div class="section-title">Pipeline</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("Transcripts", f"{stats['transcripts']}/{stats['total']}")
    c2.metric("Videos", stats["total"])

    st.markdown(f"""
    <div style="margin:8px 0;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            <span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.65rem;font-weight:700;background:#7c3aed;color:white;">Pro</span>
            <span style="font-size:0.75rem;color:#cbd5e1;">{stats['hooks_pro']} hooks · {stats['reviewed_pro']} reviewed</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
            <span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.65rem;font-weight:700;background:#0891b2;color:white;">Flash</span>
            <span style="font-size:0.75rem;color:#cbd5e1;">{stats['hooks_flash']} hooks · {stats['reviewed_flash']} reviewed</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Navigation
    st.markdown('<div class="section-title">Navigation</div>', unsafe_allow_html=True)
    _pages = ["Dashboard", "Import Hooks", "Review", "Analytics", "Dataset", "Prompt Lab"]
    _default_idx = 0
    _page_override = st.session_state.pop("page_override", None)
    if _page_override and _page_override in _pages:
        _default_idx = _pages.index(_page_override)
    page = st.radio("", _pages, index=_default_idx, label_visibility="collapsed")

    st.divider()

    # Downloads
    spreadsheet_path = EVAL_DIR / "hookcut_eval_dataset.xlsx"
    if spreadsheet_path.exists():
        with open(spreadsheet_path, "rb") as f:
            st.download_button(
                "Export Dataset", data=f.read(),
                file_name="hookcut_eval_dataset.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    st.caption(f"{datetime.now().strftime('%b %d, %Y')}")


# ── Page: Dashboard ──────────────────────────────────────────────

def page_dashboard():
    st.markdown("## Dashboard")

    batch_size, total_batches = get_batch_info()

    # ── Overall pipeline stats ────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Videos", stats["total"])
    c2.metric("Transcripts", f"{stats['transcripts']}/{stats['total']}")
    c3.metric("Pro Hooks (videos)", stats["hooks_pro"])
    c4.metric("Flash Hooks (videos)", stats["hooks_flash"])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.65rem;font-weight:700;background:#7c3aed;color:white;">Pro</span>'
            f' <span style="font-size:0.85rem;">0/{stats["total"]} reviewed</span>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.65rem;font-weight:700;background:#0891b2;color:white;">Flash</span>'
            f' <span style="font-size:0.85rem;">{stats["reviewed_flash"]}/{stats["total"]} reviewed</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Batch selector ─────────────────────────────────────────────
    # Persist selected batch in session state / query params
    _qb = st.query_params.get("batch")
    _default_batch = int(_qb) if _qb and _qb.isdigit() else st.session_state.get("selected_batch", 1)
    _default_batch = max(1, min(_default_batch, total_batches))

    tab_labels = [f"Batch {i}" for i in range(1, total_batches + 1)]

    selected_batch = st.radio(
        "Select batch",
        list(range(1, total_batches + 1)),
        index=_default_batch - 1,
        format_func=lambda x: f"Batch {x}",
        horizontal=True,
        key="batch_radio",
        label_visibility="collapsed",
    )

    st.session_state["selected_batch"] = selected_batch
    st.query_params.update(batch=str(selected_batch))

    # ── Load videos for selected batch ────────────────────────────
    data_pro = load_batch_videos("v1-pro", selected_batch)
    data_flash = load_batch_videos("v1-flash", selected_batch)
    batch = data_pro["batch"]  # video list is the same; only hook/review counts differ

    # Per-batch stats
    pro_hooks_b = sum(1 for v in batch if v["has_hooks"])
    flash_hooks_b = sum(1 for v in data_flash["batch"] if v["has_hooks"])
    pro_rev_b = sum(1 for v in batch if v["is_reviewed"])
    flash_rev_b = sum(1 for v in data_flash["batch"] if v["is_reviewed"])

    sb1, sb2, sb3, sb4 = st.columns(4)
    sb1.metric("Videos", len(batch))
    sb2.metric("Pro Hooks", pro_hooks_b)
    sb3.metric("Flash Hooks", flash_hooks_b)
    sb4.metric("Reviewed", f"{max(pro_rev_b, flash_rev_b)}/{len(batch)}")

    # Progress bars
    pc1, pc2 = st.columns(2)
    with pc1:
        pct = pro_rev_b / max(1, len(batch))
        st.progress(pct, text=f"Pro — {pro_rev_b}/{len(batch)} reviewed")
    with pc2:
        pct = flash_rev_b / max(1, len(batch))
        st.progress(pct, text=f"Flash — {flash_rev_b}/{len(batch)} reviewed")

    st.markdown("---")

    # ── Filters ────────────────────────────────────────────────────
    fc1, fc2 = st.columns(2)
    status_filter = fc1.selectbox(
        "Filter by status", ["All", "Needs Import", "Ready to Review", "Reviewed"],
        key="dash_filter",
    )
    niche_filter = fc2.selectbox(
        "Filter by niche", ["All"] + sorted(set(v["niche"] for v in batch)),
        key="dash_niche",
    )

    # ── Video rows ─────────────────────────────────────────────────
    # Header row
    st.markdown(
        '<div style="display:grid;grid-template-columns:30px 70px 1fr 160px 60px 100px 100px;'
        'gap:8px;padding:4px 0;border-bottom:2px solid #e2e8f0;font-size:0.7rem;'
        'font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#94a3b8;">'
        '<div>#</div><div>Niche</div><div>Video (click to open)</div>'
        '<div>Status</div><div></div><div>Action</div><div></div></div>',
        unsafe_allow_html=True,
    )

    visible = 0
    for i, v in enumerate(batch):
        if niche_filter != "All" and v["niche"] != niche_filter:
            continue

        status_key, status_label = get_video_status(v, active_model)

        if status_filter == "Needs Import" and status_key not in ("needs-hooks", "no-transcript"):
            continue
        if status_filter == "Ready to Review" and status_key not in ("ready",):
            continue
        if status_filter == "Reviewed" and status_key not in ("both-reviewed", "partial"):
            continue

        visible += 1

        # Transcript path — show full path if exists
        tp = v.get("transcript_path") or ""
        file_exists = Path(tp).exists() if tp else False
        if tp and file_exists:
            transcript_html = f'<div class="transcript-path" title="{tp}">📄 {tp}</div>'
        elif tp:
            transcript_html = f'<div class="transcript-path-missing" title="{tp}">📄 {Path(tp).name} (not found)</div>'
        else:
            transcript_html = '<div class="transcript-path-missing">no transcript</div>'

        cols = st.columns([0.25, 0.65, 3.5, 1.2, 0.8, 1.0, 1.0])

        with cols[0]:
            st.markdown(f'<span style="color:#94a3b8;font-size:0.8rem;">{i+1}</span>', unsafe_allow_html=True)
        with cols[1]:
            st.markdown(niche_pill(v["niche"]), unsafe_allow_html=True)
        # Build direct hrefs — no button click needed, standard browser navigation
        import_href = f"/?vid={v['video_id']}&page=Import+Hooks"
        review_href = f"/?vid={v['video_id']}&mode=review&page=Review"
        inspect_href = f"/?vid={v['video_id']}&mode=inspect&page=Review"

        with cols[2]:
            title_short = v['title'][:70] + ('…' if len(v['title']) > 70 else '')
            st.markdown(
                f'<a href="{import_href}" style="font-weight:700;color:#2563eb;text-decoration:underline;">'
                f'{v["creator_name"]} — {title_short}</a>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<span style="font-size:0.75rem;color:#94a3b8;">'
                f'{v["performance_category"].upper()} · {format_views(v["views"])} views · '
                f'{format_duration(v["duration_seconds"])}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(transcript_html, unsafe_allow_html=True)
        with cols[3]:
            st.markdown(status_badge_html(status_key, status_label), unsafe_allow_html=True)
        with cols[4]:
            st.markdown("")  # spacer
        with cols[5]:
            if status_key in ("needs-hooks", "no-transcript", "ready", "partial"):
                action_label = "Import →" if status_key in ("needs-hooks", "no-transcript") else "Review →"
                action_href = import_href if status_key in ("needs-hooks", "no-transcript") else review_href
                st.markdown(
                    f'<a href="{action_href}" class="action-link" '
                    f'style="display:block;text-align:center;padding:5px 8px;">{action_label}</a>',
                    unsafe_allow_html=True,
                )
            elif status_key == "both-reviewed":
                st.markdown(
                    f'<a href="{import_href}" class="action-link" '
                    f'style="display:block;text-align:center;padding:5px 8px;">Transcript →</a>',
                    unsafe_allow_html=True,
                )
        with cols[6]:
            if status_key in ("both-reviewed", "partial"):
                st.markdown(
                    f'<a href="{inspect_href}" class="action-link" '
                    f'style="display:block;text-align:center;padding:5px 8px;">Inspect →</a>',
                    unsafe_allow_html=True,
                )

    if visible == 0:
        st.info("No videos match the current filters.")


# ── Page: Import Hooks ───────────────────────────────────────────

def page_import():
    st.markdown("## Import Hooks")
    st.caption("Paste transcript + niche context into Gemini 3.1 Pro → paste JSON back here")

    # The video to import for MUST come from the URL query param.
    import_vid = st.query_params.get("vid") or st.session_state.get("import_video_id")

    data = load_batch_videos(active_model)
    batch = data["batch"]
    needs_import = [v for v in batch if v["has_transcript"] and not v["has_hooks"]]
    done_count = len(batch) - len(needs_import)

    # ── Pending queue (always visible) ────────────────────────────
    m = MODELS[active_model]
    with st.expander(
        f"📋 Queue: {len(needs_import)} videos need hooks ({done_count}/{len(batch)} done for {m['label']})",
        expanded=not import_vid,
    ):
        if not needs_import:
            st.success("✓ All videos in this batch have hooks!")
        else:
            # Table header
            st.markdown(
                '<div style="display:grid;grid-template-columns:1fr 1fr 2fr 80px;'
                'gap:6px;font-size:0.7rem;font-weight:700;color:#64748b;'
                'padding:4px 8px;border-bottom:1px solid #e2e8f0;margin-bottom:4px;">'
                '<span>Niche</span><span>Creator</span><span>Title</span><span>Action</span></div>',
                unsafe_allow_html=True,
            )
            for v in needs_import:
                vid = v["video_id"]
                url = f"/?vid={vid}&page=Import+Hooks&model={active_model}"
                is_current = vid == import_vid
                bg = "#eff6ff" if is_current else "white"
                border = "border-left:3px solid #3b82f6;" if is_current else ""
                st.markdown(
                    f'<div style="display:grid;grid-template-columns:1fr 1fr 2fr 80px;'
                    f'gap:6px;font-size:0.78rem;padding:5px 8px;background:{bg};'
                    f'border-radius:6px;margin-bottom:2px;{border}">'
                    f'<span>{niche_pill(v["niche"])}</span>'
                    f'<span style="color:#1e293b;font-weight:600;">{v["creator_name"][:22]}</span>'
                    f'<span style="color:#475569;">{v["title"][:55]}{"…" if len(v["title"])>55 else ""}</span>'
                    f'<a href="{url}" target="_self" style="font-size:0.72rem;color:#3b82f6;'
                    f'font-weight:700;text-decoration:none;">{"▶ current" if is_current else "→ open"}</a>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    if not import_vid:
        if not needs_import:
            st.success("All videos in the current batch have hooks imported! Switch to **Review**.")
        else:
            first = needs_import[0]
            st.info(f"Click **→ open** on any video above to start, or open the first one:")
            if st.button(f"→ Start with: {first['creator_name']} — {first['title'][:50]}", type="primary"):
                st.query_params.update(vid=first["video_id"], page="Import Hooks", model=active_model)
                st.rerun()
        return

    # Load video details
    with get_db() as conn:
        video = conn.execute("SELECT * FROM videos WHERE video_id=?", (import_vid,)).fetchone()
        transcript_row = conn.execute(
            "SELECT text FROM transcripts WHERE video_id=? AND text IS NOT NULL",
            (import_vid,),
        ).fetchone()

    if not video:
        st.error("Video not found")
        return

    video = dict(video)
    txt = transcript_row["text"] if transcript_row else None

    # ── Model banner ──────────────────────────────────────────────
    st.markdown(
        f'<div style="background:{m["bg"]};border:2px solid {m["color"]};border-radius:8px;'
        f'padding:8px 16px;margin-bottom:10px;display:flex;align-items:center;gap:12px;">'
        f'<span style="font-size:1rem;font-weight:800;color:{m["color"]};">Saving to: {m["label"]}</span>'
        f'<span style="font-size:0.78rem;color:#64748b;">Change model in the sidebar if wrong</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Video header ──────────────────────────────────────────────
    st.markdown(
        f"{niche_pill(video['niche'])} "
        f'<span style="font-size:0.8rem;color:#64748b;margin-left:6px;">{video["performance_category"].upper()}</span>'
        f' &nbsp;<span style="font-size:0.9rem;font-weight:700;color:#0f172a;">{video["creator_name"]}</span>'
        f' — <span style="font-size:0.85rem;color:#334155;">{video["title"][:80]}{"…" if len(video["title"])>80 else ""}</span>'
        f' &nbsp;<a href="{video["url"]}" target="_blank" class="yt-link">▶ YT</a>',
        unsafe_allow_html=True,
    )
    st.caption(
        f'{format_views(video["views"])} views · {format_duration(video["duration_seconds"])} · '
        f'{done_count}/{len(batch)} imported for {m["label"]}'
    )

    # ── Next video shortcut ────────────────────────────────────────
    remaining = [v for v in needs_import if v["video_id"] != import_vid]
    if remaining:
        next_v = remaining[0]
        st.markdown(
            f'<div style="font-size:0.75rem;color:#64748b;margin-bottom:4px;">'
            f'Next: <a href="/?vid={next_v["video_id"]}&page=Import+Hooks&model={active_model}" '
            f'target="_self" style="color:#3b82f6;font-weight:600;">'
            f'{next_v["creator_name"]} — {next_v["title"][:45]}</a></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Check existing hooks ──────────────────────────────────────
    with get_db() as conn:
        existing_hooks = {
            mv: conn.execute(
                "SELECT COUNT(*) FROM hooks WHERE video_id=? AND prompt_version=?",
                (import_vid, mv),
            ).fetchone()[0]
            for mv in MODEL_VERSIONS
        }

    if existing_hooks[active_model] > 0:
        st.success(
            f"✓ {MODELS[active_model]['label']} hooks already imported ({existing_hooks[active_model]} hooks). "
            f"Paste again below to overwrite."
        )

    # ── Main two-column layout: video+transcript LEFT, paste RIGHT ─
    left, right = st.columns([1, 1])

    with left:
        st.markdown(
            f'<iframe width="100%" height="270" src="https://www.youtube.com/embed/{video["video_id"]}" '
            f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
            f'gyroscope; picture-in-picture" allowfullscreen '
            f'style="border-radius:8px;display:block;"></iframe>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if txt:
            # Build context-prefixed text for Gemini
            context_prefix = (
                f"Niche: {video['niche']}\n"
                f"Creator: {video['creator_name']}\n"
                f"Title: {video['title']}\n\n"
                f"TRANSCRIPT:\n"
            )
            txt_with_context = context_prefix + txt

            st.markdown(
                f'<div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">'
                f'Transcript · {len(txt):,} chars · ~{len(txt)//4:,} tokens</div>',
                unsafe_allow_html=True,
            )

            # PRIMARY: Copy with niche context (what Gemini needs)
            render_copy_button(
                txt_with_context,
                label="📋 Copy with Niche Context (for Gemini)",
                key=f"copy_ctx_{import_vid}",
                height=44,
            )
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            # Show context prefix so user can verify
            st.markdown(
                f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:6px;'
                f'padding:8px 12px;font-family:monospace;font-size:0.72rem;color:#166534;'
                f'margin-bottom:6px;line-height:1.5;">'
                f'Niche: {video["niche"]}<br>'
                f'Creator: {video["creator_name"]}<br>'
                f'Title: {video["title"][:70]}<br>'
                f'<br>TRANSCRIPT:<br>[{len(txt):,} chars follow…]</div>',
                unsafe_allow_html=True,
            )

            # Secondary: plain transcript
            render_copy_button(txt, label="📋 Transcript only", key=f"copy_tr_{import_vid}", height=36)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            display_txt = txt[:2000] + f"\n\n… [{len(txt):,} chars total]" if len(txt) > 2000 else txt
            st.markdown(f'<div class="transcript-box" style="max-height:180px;">{display_txt}</div>', unsafe_allow_html=True)
        else:
            st.error("No transcript available for this video.")

    with right:
        st.markdown(
            f'<div style="font-size:0.8rem;font-weight:700;color:#1e293b;margin-bottom:2px;">'
            f'Paste {MODELS[active_model]["label"]} JSON output</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="font-size:0.72rem;color:#64748b;margin-bottom:8px;">'
            '1. Click <b>"Copy with Niche Context"</b> above &nbsp;'
            '2. Open <a href="https://gemini.google.com/gem/f853c9aae452" target="_blank" '
            'style="color:#3b82f6;">Gemini Gem</a> → select <b>Pro</b> model &nbsp;'
            '3. Paste &amp; send &nbsp;'
            '4. Paste JSON response below</div>',
            unsafe_allow_html=True,
        )

        json_input = st.text_area(
            "json_paste_area",
            height=320,
            placeholder='{\n  "hooks": [\n    {\n      "rank": 1,\n      "hook_text": "...",\n      ...\n    }\n  ]\n}',
            key="json_paste",
            label_visibility="collapsed",
        )

        save_col, next_col = st.columns([3, 2])
        with save_col:
            if st.button(
                f"💾 Save as {MODELS[active_model]['label']} hooks",
                type="primary",
                use_container_width=True,
                disabled=not json_input,
            ):
                try:
                    hooks = parse_hooks_json(json_input)
                    save_pasted_hooks(import_vid, active_model, hooks)
                    st.success(f"✓ Saved {len(hooks)} hooks")
                    # Auto-advance to next video
                    if remaining:
                        next_vid = remaining[0]["video_id"]
                        st.query_params.update(vid=next_vid, page="Import Hooks", model=active_model)
                    st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error saving hooks: {e}")

        with next_col:
            if remaining and st.button("⏭ Skip to Next", use_container_width=True):
                next_vid = remaining[0]["video_id"]
                st.query_params.update(vid=next_vid, page="Import Hooks", model=active_model)
                st.rerun()

        other_model = "v1-flash" if active_model == "v1-pro" else "v1-pro"
        if existing_hooks[other_model] > 0:
            st.markdown(
                f'{model_badge(other_model)} <span style="color:#16a34a;font-size:0.8rem;">already imported</span>',
                unsafe_allow_html=True,
            )
        else:
            st.caption(f"Also import for {MODELS[other_model]['label']} by switching the model in the sidebar.")

        # ── CLI shortcut ──────────────────────────────────────────
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(
            '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
            'padding:10px 14px;font-size:0.72rem;color:#64748b;">'
            '<b style="color:#1e293b;">⚡ CLI shortcut (bypass Streamlit):</b><br>'
            f'<code style="color:#7c3aed;font-size:0.7rem;">'
            f'python save_hooks_cli.py {import_vid} {active_model} /tmp/hooks.json</code>'
            '</div>',
            unsafe_allow_html=True,
        )


# ── Page: Review ─────────────────────────────────────────────────

def page_review():
    review_video_id = st.session_state.get("review_video_id")

    with get_db() as conn:
        if review_video_id:
            video = conn.execute("SELECT * FROM videos WHERE video_id = ?", (review_video_id,)).fetchone()
            video = dict(video) if video else None
        else:
            video = get_next_video_to_review(conn, active_model)

    if not video:
        with get_db() as conn:
            hooks_ready = conn.execute(
                """SELECT COUNT(DISTINCT h.video_id) FROM hooks h
                   JOIN videos v ON h.video_id = v.video_id
                   WHERE h.prompt_version = ? AND v.dataset_split = 'train'
                     AND v.video_id NOT IN (SELECT video_id FROM video_reviews WHERE prompt_version = ?)""",
                (active_model, active_model),
            ).fetchone()[0]

        if hooks_ready == 0:
            st.info("No videos ready for review. Import hooks first via the **Import Hooks** page.")
        else:
            st.info(f"{hooks_ready} videos ready for review with {MODELS[active_model]['label']}. Go to Dashboard to pick one.")
        return

    inspect_mode = st.session_state.get("review_mode") == "inspect"

    # Nav bar
    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        if st.button("Back to Dashboard"):
            st.session_state.pop("review_video_id", None)
            st.session_state.pop("review_mode", None)
            st.query_params.clear()
            st.rerun()
    with nav2:
        st.markdown(
            f"{model_badge(active_model)} "
            f"{'Inspecting' if inspect_mode else 'Reviewing'} hooks",
            unsafe_allow_html=True,
        )
    with nav3:
        if not inspect_mode:
            if st.button("Skip"):
                with get_db() as conn:
                    next_v = conn.execute(
                        """SELECT video_id FROM videos
                           WHERE dataset_split = 'train' AND review_order > ?
                             AND video_id IN (SELECT video_id FROM hooks WHERE prompt_version = ?)
                             AND video_id NOT IN (SELECT video_id FROM video_reviews WHERE prompt_version = ?)
                           ORDER BY review_order LIMIT 1""",
                        (video.get("review_order", 0), active_model, active_model),
                    ).fetchone()
                if next_v:
                    st.session_state["review_video_id"] = next_v["video_id"]
                    st.query_params.update(vid=next_v["video_id"], mode="review", page="Review")
                else:
                    st.session_state.pop("review_video_id", None)
                    st.query_params.clear()
                st.rerun()

    st.markdown("---")

    # Video header
    st.markdown(
        f"{niche_pill(video['niche'])} "
        f"<span style='font-size:0.8rem;color:#64748b;margin-left:8px;'>{video['performance_category'].upper()}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(f"### {video['creator_name']}")
    st.markdown(f"**{video['title']}**")

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Views", format_views(video["views"]))
    s2.metric("Likes", format_views(video["likes"]))
    s3.metric("Duration", format_duration(video["duration_seconds"]))
    s4.metric("Views/Day", f"{video.get('views_per_day', 0):.0f}")
    with s5:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<a href="{video["url"]}" target="_blank" class="yt-link" style="font-size:0.85rem;padding:5px 12px;">▶ Watch on YouTube</a>',
            unsafe_allow_html=True,
        )

    # Embedded video
    st.markdown(
        f'<iframe width="100%" height="380" src="https://www.youtube.com/embed/{video["video_id"]}" '
        f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
        f'gyroscope; picture-in-picture" allowfullscreen style="border-radius:10px;"></iframe>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Load hooks
    with get_db() as conn:
        hooks = get_hooks_for_video(conn, video["video_id"], active_model)

    if not hooks:
        st.warning(f"No hooks found for {MODELS[active_model]['label']}. Import them first.")
        if st.button("Go to Import", type="primary"):
            st.session_state["import_video_id"] = video["video_id"]
            st.session_state["page_override"] = "Import Hooks"
            st.query_params.update(vid=video["video_id"], page="Import Hooks")
            st.rerun()
        return

    # Load past reviews if inspecting
    past_reviews = {}
    past_video_review = None
    if inspect_mode:
        with get_db() as conn:
            for h in hooks:
                r = conn.execute(
                    "SELECT * FROM reviews WHERE hook_id = ? ORDER BY created_at DESC LIMIT 1",
                    (h["id"],),
                ).fetchone()
                if r:
                    past_reviews[h["id"]] = dict(r)
            vr = conn.execute(
                "SELECT * FROM video_reviews WHERE video_id = ? AND prompt_version = ? ORDER BY reviewed_at DESC LIMIT 1",
                (video["video_id"], active_model),
            ).fetchone()
            past_video_review = dict(vr) if vr else None

    # Hook display
    if inspect_mode:
        st.markdown(f"### Hooks ({len(hooks)}) — Read Only")
    else:
        st.markdown(f"### Hooks ({len(hooks)})")
        st.caption("Rate each hook, then submit at the bottom.")

    reviews_data = {}

    for h in hooks:
        scores = json.loads(h["scores"]) if isinstance(h["scores"], str) else (h["scores"] or {})
        algo = json.loads(h["algorithm_dynamics"]) if isinstance(h["algorithm_dynamics"], str) else (h["algorithm_dynamics"] or {})
        viewer_psych = json.loads(h["viewer_psychology"]) if isinstance(h["viewer_psychology"], str) else (h["viewer_psychology"] or {})

        dur = f"{h['duration_seconds']:.0f}s" if h["duration_seconds"] else "?"

        with st.container():
            st.markdown(f"""
            <div class="hook-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <div>
                        <span style="font-size:1.1rem;font-weight:700;color:#0f172a;">Hook {h['rank']}</span>
                        <span style="margin-left:8px;font-size:0.8rem;padding:2px 8px;background:#f1f5f9;border-radius:4px;color:#475569;">{h['hook_type']}</span>
                        <span style="margin-left:4px;font-size:0.8rem;padding:2px 8px;background:#f1f5f9;border-radius:4px;color:#475569;">{h['funnel_role']}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:0.8rem;color:#64748b;">{h['start_time']} — {h['end_time']} ({dur})</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Hook text
            st.info(h["hook_text"])

            # Scores row
            score_left, score_right = st.columns([3, 1])
            with score_left:
                if scores:
                    score_html = ""
                    for dim, val in scores.items():
                        label = dim.replace("_", " ").title()
                        score_html += score_bar(label, val)
                    st.markdown(score_html, unsafe_allow_html=True)

            with score_right:
                st.markdown(f"""
                <div style="text-align:center;padding:8px;">
                    <div style="font-size:0.7rem;color:#64748b;">ATTENTION</div>
                    <div style="font-size:1.6rem;font-weight:800;color:#0f172a;">{h['attention_score']}</div>
                    <div style="font-size:0.7rem;color:#64748b;margin-top:8px;">VIRALITY</div>
                    <div style="font-size:1.6rem;font-weight:800;color:#7c3aed;">{h['virality_score']}</div>
                </div>
                """, unsafe_allow_html=True)

                start_s = int(h.get("start_seconds", 0))
                st.markdown(
                    f'<a href="https://www.youtube.com/watch?v={video["video_id"]}&t={start_s}s" '
                    f'target="_blank" style="display:block;text-align:center;text-decoration:none;'
                    f'padding:6px 12px;border-radius:6px;border:1px solid #3b82f6;color:#3b82f6;'
                    f'font-size:0.8rem;margin-top:4px;">Play from {h["start_time"]}</a>',
                    unsafe_allow_html=True,
                )

            # LLM analysis popover
            with st.popover("LLM Analysis", use_container_width=True):
                if h.get("justification"):
                    st.markdown(f"**Justification:** {h['justification']}")
                if h.get("cognitive_tension"):
                    st.markdown(f"**Cognitive Tension:** {h['cognitive_tension']}")
                if h.get("improvement_suggestion"):
                    st.markdown(f"**Creator Tip:** {h['improvement_suggestion']}")
                if algo:
                    for k, v_val in algo.items():
                        st.markdown(f"**{k.replace('_', ' ').title()}:** {v_val}")
                if viewer_psych:
                    for k, v_val in viewer_psych.items():
                        st.markdown(f"**{k.replace('_', ' ').title()}:** {v_val}")

            # Rating area
            if inspect_mode:
                pr = past_reviews.get(h["id"])
                if pr:
                    rc1, rc2, rc3 = st.columns(3)
                    with rc1:
                        st.markdown(f"**Rating:** {stars_html(pr['rating'])}", unsafe_allow_html=True)
                    with rc2:
                        st.markdown(f"**Boundaries:** {pr['boundary_accuracy'].replace('_', ' ').title()}")
                    with rc3:
                        st.markdown(f"**Would Pick:** {pr['would_pick'].title()}")
                    if pr.get("justification"):
                        st.caption(f"Notes: {pr['justification']}")
                else:
                    st.caption("No review recorded.")
            else:
                rc1, rc2, rc3 = st.columns(3)
                with rc1:
                    rating = st.select_slider(
                        "Rating", options=[1, 2, 3, 4, 5], value=3,
                        format_func=lambda x: ["Terrible", "Poor", "OK", "Good", "Excellent"][x-1],
                        key=f"rating_{h['id']}",
                    )
                with rc2:
                    boundary = st.radio(
                        "Boundaries", ["perfect", "slightly_off", "wrong"],
                        key=f"boundary_{h['id']}", horizontal=True,
                        format_func=lambda x: x.replace("_", " ").title(),
                    )
                with rc3:
                    would_pick = st.radio(
                        "Would Pick?", ["yes", "maybe", "no"],
                        index=1, key=f"pick_{h['id']}", horizontal=True,
                        format_func=str.title,
                    )

                justification = st.text_input(
                    "Notes", key=f"just_{h['id']}",
                    placeholder="What makes this hook good/bad?",
                )

                reviews_data[h["id"]] = {
                    "rating": rating, "boundary_accuracy": boundary,
                    "would_pick": would_pick, "justification": justification,
                }

            st.markdown("---")

    # Inspect mode: show overall feedback
    if inspect_mode:
        if past_video_review and past_video_review.get("overall_feedback"):
            st.markdown("#### Overall Notes")
            st.caption(past_video_review["overall_feedback"])
        return

    # Missed hooks
    with st.expander("Report Missed Hooks", expanded=False):
        st.caption("Flag strong moments the engine missed.")
        n_missed = st.number_input("How many?", 0, 10, 0, key="n_missed")
        missed_hooks_data = []
        for i in range(int(n_missed)):
            mc1, mc2 = st.columns([1, 3])
            ts = mc1.text_input(f"Time #{i+1}", placeholder="4:32-4:50", key=f"missed_ts_{i}")
            desc = mc2.text_input(f"Desc #{i+1}", placeholder="Strong hook about...", key=f"missed_desc_{i}")
            if ts and desc:
                missed_hooks_data.append({"timestamp_range": ts, "description": desc})

    # Overall feedback
    overall_feedback = st.text_area(
        "Overall Notes",
        placeholder="Patterns, transcript quality, content observations...",
        height=80, key="overall_feedback",
    )

    # Submit
    sub1, sub2 = st.columns([3, 1])
    with sub1:
        if st.button("Submit & Next", type="primary", use_container_width=True):
            data = load_batch_videos(active_model)
            batch_number = data["batch_num"]

            with get_db() as conn:
                for hook_id, review in reviews_data.items():
                    insert_review(conn, hook_id=hook_id, **review)
                for mh in missed_hooks_data:
                    insert_missed_hook(conn, video_id=video["video_id"], prompt_version=active_model, **mh)
                insert_video_review(
                    conn, video_id=video["video_id"], prompt_version=active_model,
                    overall_feedback=overall_feedback, batch_number=batch_number,
                )

            st.session_state.pop("review_video_id", None)
            st.session_state.pop("review_mode", None)
            st.query_params.clear()
            st.toast("Review saved!")
            st.rerun()

    with sub2:
        if st.button("Submit & Stay", use_container_width=True):
            data = load_batch_videos(active_model)
            batch_number = data["batch_num"]

            with get_db() as conn:
                for hook_id, review in reviews_data.items():
                    insert_review(conn, hook_id=hook_id, **review)
                for mh in missed_hooks_data:
                    insert_missed_hook(conn, video_id=video["video_id"], prompt_version=active_model, **mh)
                insert_video_review(
                    conn, video_id=video["video_id"], prompt_version=active_model,
                    overall_feedback=overall_feedback, batch_number=batch_number,
                )

            st.toast("Review saved!")
            st.rerun()


# ── Page: Analytics ──────────────────────────────────────────────

def page_analytics():
    st.markdown("## Analytics")

    # Model comparison header
    tab_single, tab_compare = st.tabs(["Single Model", "Pro vs Flash"])

    with tab_single:
        with get_db() as conn:
            batches = conn.execute(
                "SELECT DISTINCT batch_number FROM video_reviews ORDER BY batch_number"
            ).fetchall()

        if not batches:
            st.info("No reviews yet. Complete some reviews to see analytics.")

            # Pipeline overview
            stats = load_pipeline_stats()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Videos", stats["total"])
            c2.metric("Transcripts", stats["transcripts"])
            c3.metric("Pro Hooks", stats["hooks_pro"])
            c4.metric("Flash Hooks", stats["hooks_flash"])

            with get_db() as conn:
                niche_data = conn.execute(
                    "SELECT niche, COUNT(*) as count FROM videos GROUP BY niche ORDER BY count DESC"
                ).fetchall()
            if niche_data:
                df = pd.DataFrame([dict(r) for r in niche_data])
                fig = px.bar(df, x="niche", y="count", color="niche", title="Videos by Niche")
                fig.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig, use_container_width=True)
            return

        batch_options = [b["batch_number"] for b in batches]
        selected_batch = st.selectbox("Batch", batch_options, index=len(batch_options) - 1)

        analysis = analyze_batch(selected_batch)
        if "error" in analysis:
            st.error(analysis["error"])
            return

        # Top metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Videos", analysis["total_videos_reviewed"])
        m2.metric("Hooks", analysis["total_hooks_reviewed"])
        m3.metric("Avg Rating", f"{analysis['avg_rating']:.1f}/5")
        m4.metric("Pick Rate", f"{analysis['would_pick'].get('yes', 0)}%")
        m5.metric("Failures", analysis["failure_count"])

        st.markdown("---")

        # Charts
        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("#### Rating Distribution")
            rating_data = pd.DataFrame([
                {"Rating": f"{k}★", "Count": v, "rating_num": k}
                for k, v in sorted(analysis["rating_distribution"].items())
            ])
            if not rating_data.empty:
                colors = {1: "#ef4444", 2: "#f97316", 3: "#eab308", 4: "#22c55e", 5: "#10b981"}
                fig = px.bar(rating_data, x="Rating", y="Count", color="rating_num",
                            color_discrete_map={k: colors[k] for k in colors})
                fig.update_layout(showlegend=False, height=280)
                st.plotly_chart(fig, use_container_width=True)

        with ch2:
            st.markdown("#### Would Pick?")
            if analysis["would_pick"]:
                wp_data = pd.DataFrame([
                    {"Choice": k.title(), "Percentage": v}
                    for k, v in analysis["would_pick"].items()
                ])
                fig = px.pie(wp_data, values="Percentage", names="Choice",
                            color="Choice", color_discrete_map={
                                "Yes": "#22c55e", "Maybe": "#f59e0b", "No": "#ef4444"
                            }, hole=0.4)
                fig.update_layout(height=280)
                st.plotly_chart(fig, use_container_width=True)

        ch3, ch4 = st.columns(2)
        with ch3:
            st.markdown("#### Boundary Accuracy")
            if analysis["boundary_accuracy"]:
                ba_data = pd.DataFrame([
                    {"Accuracy": k.replace("_", " ").title(), "Percentage": v}
                    for k, v in analysis["boundary_accuracy"].items()
                ])
                fig = px.pie(ba_data, values="Percentage", names="Accuracy",
                            color="Accuracy", color_discrete_map={
                                "Perfect": "#22c55e", "Slightly Off": "#f59e0b", "Wrong": "#ef4444"
                            }, hole=0.4)
                fig.update_layout(height=280)
                st.plotly_chart(fig, use_container_width=True)

        with ch4:
            st.markdown("#### LLM vs Human Calibration")
            if analysis["llm_score_calibration"]:
                cal_data = pd.DataFrame([
                    {"Human Rating": f"{k}★", "LLM Score": v}
                    for k, v in analysis["llm_score_calibration"].items()
                ])
                fig = px.bar(cal_data, x="Human Rating", y="LLM Score",
                            color="LLM Score", color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"])
                fig.update_layout(height=280, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # Tables
        t1, t2 = st.columns(2)
        with t1:
            st.markdown("#### By Niche")
            niche_rows = [
                {"Niche": n, "Hooks": s["total"], "Avg": s["avg_rating"],
                 "Pick %": s["pick_rate"], "Boundary %": s["boundary_accuracy_pct"]}
                for n, s in sorted(analysis["by_niche"].items())
            ]
            if niche_rows:
                st.dataframe(pd.DataFrame(niche_rows), use_container_width=True, hide_index=True)

        with t2:
            st.markdown("#### By Hook Type")
            type_rows = [
                {"Type": ht, "N": s["total"], "Avg": s["avg_rating"], "Pick %": s["pick_rate"]}
                for ht, s in sorted(analysis["by_hook_type"].items(), key=lambda x: -x[1]["avg_rating"])
            ]
            if type_rows:
                st.dataframe(pd.DataFrame(type_rows), use_container_width=True, hide_index=True)

    with tab_compare:
        st.markdown("### Pro vs Flash Comparison")

        result = compare_versions("v1-pro", "v1-flash")
        if "error" in result:
            st.info("Need reviews for both models to compare. Complete reviews for both Pro and Flash first.")
            return

        # Side-by-side metrics
        c1, c2 = st.columns(2)
        for col, key, ver in [(c1, "v1", "v1-pro"), (c2, "v2", "v1-flash")]:
            with col:
                st.markdown(model_badge(ver), unsafe_allow_html=True)
                s = result[key]
                st.metric("Reviews", s["total_reviews"])
                st.metric("Avg Rating", s["avg_rating"])
                st.metric("Pick Rate", f"{s['would_pick_yes_pct']}%")
                st.metric("Perfect Boundary", f"{s['boundary_perfect_pct']}%")

        st.markdown("---")
        st.markdown("#### Delta (Flash - Pro)")
        d = result["improvement"]
        dc1, dc2, dc3 = st.columns(3)
        dc1.metric("Rating", f"{d['avg_rating_delta']:+.2f}")
        dc2.metric("Pick Rate", f"{d['pick_rate_delta']:+.1f}%")
        dc3.metric("Boundary", f"{d['boundary_delta']:+.1f}%")


# ── Page: Dataset Explorer ───────────────────────────────────────

def page_dataset():
    st.markdown("## Dataset Explorer")

    with get_db() as conn:
        videos = conn.execute(
            """SELECT v.*, c.subscriber_count, c.tier
               FROM videos v JOIN creators c ON v.creator_id = c.id
               ORDER BY v.niche, v.creator_name, v.review_order"""
        ).fetchall()

        creators = conn.execute(
            """SELECT c.name, c.niche, c.tier, c.subscriber_count, c.channel_url,
                      COUNT(v.id) as video_count
               FROM creators c LEFT JOIN videos v ON c.id = v.creator_id
               GROUP BY c.id ORDER BY c.niche, c.subscriber_count DESC"""
        ).fetchall()

        transcript_stats = conn.execute(
            """SELECT COUNT(*) as total,
                 SUM(CASE WHEN text IS NOT NULL THEN 1 ELSE 0 END) as done,
                 SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as failed
               FROM transcripts"""
        ).fetchone()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Videos", len(videos))
    c2.metric("Creators", len(creators))
    c3.metric("Niches", len(set(v["niche"] for v in videos)))
    c4.metric("Transcripts", transcript_stats["done"] if transcript_stats else 0)
    c5.metric("Failed", transcript_stats["failed"] if transcript_stats else 0)

    tab1, tab2, tab3 = st.tabs(["Creators", "Videos", "Distribution"])

    with tab1:
        cr_df = pd.DataFrame([dict(c) for c in creators])
        if not cr_df.empty:
            cr_df["subscriber_count"] = cr_df["subscriber_count"].apply(
                lambda x: format_views(x) if x else "?"
            )
            st.dataframe(
                cr_df[["name", "niche", "tier", "subscriber_count", "video_count"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "name": "Creator", "niche": "Niche", "tier": "Tier",
                    "subscriber_count": "Subscribers", "video_count": "Videos",
                },
            )

    with tab2:
        f1, f2 = st.columns(2)
        split_f = f1.selectbox("Split", ["All", "train", "test"], key="ds_split")
        niche_f = f2.selectbox("Niche", ["All"] + sorted(set(v["niche"] for v in videos)), key="ds_niche")

        filtered = [dict(v) for v in videos]
        if split_f != "All":
            filtered = [v for v in filtered if v["dataset_split"] == split_f]
        if niche_f != "All":
            filtered = [v for v in filtered if v["niche"] == niche_f]

        df = pd.DataFrame(filtered)
        if not df.empty:
            df["views"] = df["views"].apply(format_views)
            df["duration"] = df["duration_seconds"].apply(format_duration)
            st.dataframe(
                df[["niche", "creator_name", "title", "views", "duration",
                    "performance_category", "dataset_split", "url"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "url": st.column_config.LinkColumn("YouTube", display_text="Watch"),
                    "niche": "Niche", "creator_name": "Creator",
                    "title": "Title", "views": "Views", "duration": "Duration",
                    "performance_category": "Category", "dataset_split": "Split",
                },
            )

    with tab3:
        d1, d2 = st.columns(2)
        with d1:
            niche_counts = pd.DataFrame([
                {"Niche": v["niche"], "Count": 1} for v in videos
            ]).groupby("Niche").sum().reset_index()
            fig = px.bar(niche_counts, x="Niche", y="Count", color="Niche", title="Videos per Niche")
            fig.update_layout(showlegend=False, height=320)
            st.plotly_chart(fig, use_container_width=True)

        with d2:
            cat_counts = pd.DataFrame([
                {"Category": v["performance_category"].title(), "Count": 1} for v in videos
            ]).groupby("Category").sum().reset_index()
            fig = px.pie(cat_counts, values="Count", names="Category",
                        title="Performance Categories", hole=0.4)
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)

        split_counts = pd.DataFrame([
            {"Split": v["dataset_split"].title(), "Niche": v["niche"], "Count": 1}
            for v in videos
        ]).groupby(["Niche", "Split"]).sum().reset_index()
        fig = px.bar(split_counts, x="Niche", y="Count", color="Split",
                    barmode="group", title="Train/Test Split by Niche")
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)


# ── Page: Prompt Lab ─────────────────────────────────────────────

def _get_live_prompt(niche: str, language: str) -> str:
    """Generate the current v1 prompt with a placeholder transcript."""
    try:
        sys.path.insert(0, str(EVAL_DIR.parent.parent))
        from app.llm.prompts.hook_identification import build_hook_prompt
        placeholder = (
            "[PASTE TRANSCRIPT HERE]\n\n"
            "# Instructions for use:\n"
            "# 1. Delete this placeholder block\n"
            "# 2. Paste the full transcript text from the eval tool\n"
            "# 3. Submit to Gemini\n"
            "# 4. Copy the JSON response back into the eval tool's Import Hooks page"
        )
        return build_hook_prompt(niche, placeholder, language)
    except Exception as e:
        return f"[Error generating prompt: {e}]"


def page_prompt_lab():
    st.markdown("## Prompt Lab")

    with get_db() as conn:
        versions = conn.execute("SELECT * FROM prompt_versions ORDER BY created_at").fetchall()

    versions = [dict(v) for v in versions] if versions else []

    tab1, tab2, tab3 = st.tabs(["Copy Prompt", "Versions", "Compare"])

    # ── Tab 1: Copy Prompt ──────────────────────────────────────
    with tab1:
        st.markdown("### Ready-to-Paste Prompt")
        st.caption(
            "Select the niche and language matching the video you're analysing, "
            "then copy the full prompt into your Gemini Pro or Flash Gem. "
            "Replace the placeholder at the bottom with the transcript."
        )

        NICHE_LIST = [
            "Finance", "Tech / AI", "Entrepreneurship", "Education",
            "Podcast", "Fitness", "Drama / Commentary",
        ]
        LANG_LIST = ["English", "Hindi", "Telugu"]

        cfg1, cfg2, cfg3 = st.columns([2, 1, 1])
        with cfg1:
            sel_niche = st.selectbox("Niche", NICHE_LIST, index=0, key="pl_niche")
        with cfg2:
            sel_lang = st.selectbox("Language", LANG_LIST, index=0, key="pl_lang")
        with cfg3:
            interview_mode = st.checkbox("Interview mode", value=False, key="pl_interview")

        try:
            sys.path.insert(0, str(EVAL_DIR.parent.parent))
            from app.llm.prompts.hook_identification import build_hook_prompt
            TRANSCRIPT_PLACEHOLDER = (
                "[PASTE TRANSCRIPT HERE]\n\n"
                "──────────────────────────────────────────────\n"
                "HOW TO USE THIS PROMPT:\n"
                "1. Copy the full transcript from the Import Hooks page\n"
                "2. Delete everything from [PASTE TRANSCRIPT HERE] downward\n"
                "3. Paste the transcript text in its place\n"
                "4. Submit to Gemini Pro or Flash\n"
                "5. Copy the JSON response → paste back into Import Hooks\n"
                "──────────────────────────────────────────────"
            )
            prompt_text = build_hook_prompt(sel_niche, TRANSCRIPT_PLACEHOLDER, sel_lang, interview_mode=interview_mode)
            prompt_len = len(prompt_text)

            st.markdown("---")

            # Stats row
            s1, s2, s3 = st.columns(3)
            s1.metric("Characters", f"{prompt_len:,}")
            s2.metric("Est. tokens", f"~{prompt_len // 4:,}")
            s3.metric("Niche", sel_niche)

            st.markdown(
                "<div class='section-title' style='margin-top:12px;'>Full Prompt — select all & copy (Ctrl+A, Ctrl+C)</div>",
                unsafe_allow_html=True,
            )
            st.text_area(
                "prompt_copy_area",
                value=prompt_text,
                height=500,
                label_visibility="collapsed",
                key="prompt_full_text",
            )

            st.info(
                "**Workflow:** Copy transcript from Import Hooks → paste into Gemini Gem → "
                "replace `[PASTE TRANSCRIPT HERE]` → submit → copy JSON → paste back in Import Hooks"
            )

        except Exception as e:
            st.error(f"Could not generate prompt: {e}")
            st.caption("Make sure you're running from the hookcut-backend directory.")

    # ── Tab 2: Versions ─────────────────────────────────────────
    with tab2:
        st.markdown("### Registered Prompt Versions")

        if not versions:
            st.info("No prompt versions registered yet.")
        else:
            for v in versions:
                with get_db() as conn:
                    hook_stats = conn.execute(
                        "SELECT COUNT(*) as hooks, COUNT(DISTINCT video_id) as videos FROM hooks WHERE prompt_version = ?",
                        (v["version"],),
                    ).fetchone()
                    review_stats = conn.execute(
                        """SELECT COUNT(*) as reviews, AVG(r.rating) as avg_rating
                           FROM reviews r JOIN hooks h ON r.hook_id = h.id WHERE h.prompt_version = ?""",
                        (v["version"],),
                    ).fetchone()

                hook_stats = dict(hook_stats)
                review_stats = dict(review_stats)

                badge_html = model_badge(v["version"]) if v["version"] in MODELS else f'<span class="badge badge-needs-hooks">{v["version"]}</span>'
                label = f'{v["version"]} — {v["description"]}'

                with st.expander(label, expanded=(v == versions[-1])):
                    st.markdown(badge_html, unsafe_allow_html=True)

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Hooks", hook_stats["hooks"])
                    c2.metric("Videos", hook_stats["videos"])
                    c3.metric("Reviews", review_stats["reviews"])
                    c4.metric(
                        "Avg Rating",
                        f"{review_stats['avg_rating']:.2f}" if review_stats["avg_rating"] else "N/A",
                    )

                    st.caption(f"Hash: `{v['prompt_hash']}` · Created: {v['created_at']}")

                    if st.toggle("Show full prompt snapshot", key=f"show_{v['version']}"):
                        snapshot = v.get("prompt_snapshot") or ""
                        if snapshot:
                            st.text_area(
                                "Prompt snapshot",
                                value=snapshot,
                                height=400,
                                label_visibility="collapsed",
                                key=f"snap_{v['version']}",
                            )
                        else:
                            st.warning("No prompt snapshot stored for this version.")

    # ── Tab 3: Compare ──────────────────────────────────────────
    with tab3:
        st.markdown("### Version Comparison")

        if len(versions) < 2:
            st.info("Need at least 2 versions to compare. Currently only v1 variants exist.")
        else:
            v_names = [v["version"] for v in versions]
            c1, c2 = st.columns(2)
            va = c1.selectbox("Version A", v_names, index=0)
            vb = c2.selectbox("Version B", v_names, index=min(1, len(v_names) - 1))

            if st.button("Compare", type="primary"):
                result = compare_versions(va, vb)
                if "error" in result:
                    st.error(result["error"])
                else:
                    c1, c2 = st.columns(2)
                    for col, key, label in [(c1, "v1", va), (c2, "v2", vb)]:
                        with col:
                            badge = model_badge(label) if label in MODELS else ""
                            st.markdown(f"#### {badge} {label}", unsafe_allow_html=True)
                            s = result[key]
                            st.metric("Reviews", s["total_reviews"])
                            st.metric("Avg Rating", s["avg_rating"])
                            st.metric("Pick Rate", f"{s['would_pick_yes_pct']}%")
                            st.metric("Perfect Boundary", f"{s['boundary_perfect_pct']}%")

                    st.markdown("---")
                    st.markdown("#### Delta (B − A)")
                    d = result["improvement"]
                    dc1, dc2, dc3 = st.columns(3)
                    dc1.metric("Rating", f"{d['avg_rating_delta']:+.2f}")
                    dc2.metric("Pick Rate", f"{d['pick_rate_delta']:+.1f}%")
                    dc3.metric("Boundary", f"{d['boundary_delta']:+.1f}%")


# ── Router ────────────────────────────────────────────────────────

if st.session_state.get("nav_to_review"):
    st.session_state.pop("nav_to_review")
    page_review()
elif page == "Dashboard":
    page_dashboard()
elif page == "Import Hooks":
    page_import()
elif page == "Review":
    page_review()
elif page == "Analytics":
    page_analytics()
elif page == "Dataset":
    page_dataset()
elif page == "Prompt Lab":
    page_prompt_lab()
