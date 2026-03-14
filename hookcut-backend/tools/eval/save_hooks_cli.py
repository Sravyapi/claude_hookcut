#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct DB hook insertion — no Streamlit needed.

Usage:
    python save_hooks_cli.py <video_id> <prompt_version> <json_file>
    python save_hooks_cli.py <video_id> <prompt_version> -  # read JSON from stdin

Examples:
    python save_hooks_cli.py GhXgTFACCto v1-pro /tmp/hooks.json
    echo '{"hooks":[...]}' | python save_hooks_cli.py GhXgTFACCto v1-pro -
    python save_hooks_cli.py GhXgTFACCto v1-pro - <<< "$JSON_VAR"
"""

import json
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_EVAL_DIR))

from db import get_db, insert_hook, insert_prompt_version


PROMPT_VERSION_LABELS = {
    "v1-pro": "Gemini 3.1 Pro (browser Gem)",
    "v1-flash": "Gemini 2.5 Flash (browser Gem)",
}


def ensure_prompt_version(conn, version: str):
    row = conn.execute("SELECT id FROM prompt_versions WHERE version=?", (version,)).fetchone()
    if not row:
        insert_prompt_version(
            conn,
            version=version,
            description=PROMPT_VERSION_LABELS.get(version, version),
            prompt_hash="browser-gem",
            prompt_snapshot="(generated via Gemini Gem browser automation)",
            parent_version=None,
        )


def save_hooks(video_id: str, prompt_version: str, hooks_json: dict) -> int:
    """Insert hooks from parsed JSON into DB. Returns number of hooks saved."""
    hooks = hooks_json.get("hooks", [])
    if not hooks:
        raise ValueError("JSON has no 'hooks' array")

    with get_db() as conn:
        ensure_prompt_version(conn, prompt_version)

        # Delete existing hooks for this video+version (overwrite)
        conn.execute(
            "DELETE FROM hooks WHERE video_id=? AND prompt_version=?",
            (video_id, prompt_version),
        )

        for h in hooks:
            # Parse start/end seconds from timestamp strings
            start_seconds = _ts_to_seconds(str(h.get("start_time", "0:00")))
            end_seconds = _ts_to_seconds(str(h.get("end_time", "0:00")))
            is_composite = "+" in str(h.get("start_time", ""))

            insert_hook(
                conn,
                video_id=video_id,
                prompt_version=prompt_version,
                rank=int(h.get("rank", 0)),
                hook_text=str(h.get("hook_text", "")),
                start_time=str(h.get("start_time", "")),
                end_time=str(h.get("end_time", "")),
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                duration_seconds=max(0, end_seconds - start_seconds),
                hook_type=str(h.get("hook_type", "")),
                funnel_role=str(h.get("funnel_role", "")),
                cognitive_tension=str(h.get("cognitive_tension", "")),
                scores=h.get("scores", {}),
                attention_score=float(h.get("attention_score", 0)),
                virality_score=float(h.get("virality_score", 0)),
                justification=str(h.get("justification", "")),
                algorithm_dynamics=h.get("algorithm_dynamics", {}),
                viewer_psychology=h.get("viewer_psychology", {}),
                improvement_suggestion=str(h.get("improvement_suggestion", "")),
                is_composite=is_composite,
            )

    return len(hooks)


def _ts_to_seconds(ts: str) -> float:
    """Convert 'M:SS.mm' or 'H:MM:SS.mm' to seconds."""
    try:
        ts = ts.strip()
        parts = ts.split(":")
        if len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        elif len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        return float(ts)
    except Exception:
        return 0.0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    video_id = sys.argv[1]
    prompt_version = sys.argv[2]
    json_source = sys.argv[3]

    # Read JSON
    if json_source == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(json_source).read_text()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        n = save_hooks(video_id, prompt_version, data)
        print(f"✓ Saved {n} hooks for {video_id} (version: {prompt_version})")
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
