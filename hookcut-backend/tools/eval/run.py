#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HookCut Eval Framework - Single entry point.

Launches the review UI immediately. Transcript fetching and hook generation
run in a background process so the UI is usable right away.

Usage:
    python3 run.py              # Launch UI + background pipeline
    python3 run.py --no-ui      # Run pipeline only (transcripts + hooks), no UI
"""

import os
import subprocess
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EVAL_DIR.parent.parent
VENV_PYTHON = EVAL_DIR / ".venv" / "bin" / "python3"


def _relaunch_in_venv():
    """If we're not running inside the eval venv, re-exec ourselves with it."""
    if not VENV_PYTHON.exists():
        print(f"ERROR: Eval venv not found at {VENV_PYTHON}")
        print(f"Create it with: python3 -m venv {EVAL_DIR / '.venv'}")
        sys.exit(1)

    eval_venv_prefix = str((EVAL_DIR / ".venv").resolve())
    if sys.prefix == eval_venv_prefix:
        return

    venv_bin = str(VENV_PYTHON)
    os.execv(venv_bin, [venv_bin] + sys.argv)


# Auto-activate venv before anything else
_relaunch_in_venv()

# Now we're guaranteed to be in the venv - set up paths
sys.path.insert(0, str(EVAL_DIR))
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(str(EVAL_DIR))


def run_pipeline(prompt_version="v1"):
    """Run transcript fetch + hook generation (blocking). Used by background worker."""
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")

    from db import get_db

    # Step 1: Transcripts
    with get_db() as conn:
        missing = conn.execute(
            """SELECT COUNT(*) FROM videos v
               LEFT JOIN transcripts t ON v.video_id = t.video_id
               WHERE t.id IS NULL"""
        ).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]

    if missing > 0:
        print(f"[pipeline] Fetching {missing}/{total} transcripts...")
        from transcript_fetcher import fetch_all_missing
        fetch_all_missing()
    else:
        print(f"[pipeline] All {total} transcripts ready.")

    # Step 2: Hooks
    with get_db() as conn:
        pv = conn.execute(
            "SELECT version FROM prompt_versions WHERE version=?", (prompt_version,)
        ).fetchone()
        if not pv:
            print(f"[pipeline] Registering prompt version '{prompt_version}'...")
            from hook_generator import register_prompt_version
            register_prompt_version(prompt_version, "Production prompt - initial version")

        missing = conn.execute(
            """SELECT COUNT(*) FROM videos v
               JOIN transcripts t ON v.video_id = t.video_id
               WHERE t.text IS NOT NULL
                 AND v.video_id NOT IN (
                     SELECT video_id FROM hooks WHERE prompt_version = ?
                 )""",
            (prompt_version,),
        ).fetchone()[0]
        total_with = conn.execute(
            "SELECT COUNT(*) FROM transcripts WHERE text IS NOT NULL"
        ).fetchone()[0]

    if missing > 0:
        print(f"[pipeline] Generating hooks for {missing}/{total_with} videos...")
        from hook_generator import generate_all
        generate_all(prompt_version)
    else:
        print(f"[pipeline] All {total_with} hook sets ready.")

    print("[pipeline] Done.")


def step_ui():
    """Launch Streamlit review UI."""
    app_path = EVAL_DIR / "app.py"
    print(f"\n[ui] Launching review UI at http://localhost:8501 ...")
    print("[ui] Press Ctrl+C to stop.\n")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path),
         "--server.headless", "true"],
        cwd=str(EVAL_DIR),
    )


def main():
    args = set(sys.argv[1:])
    no_ui = "--no-ui" in args

    print("=" * 60)
    print("  HookCut Eval Framework")
    print("=" * 60)

    if no_ui:
        run_pipeline()
        print("\nDone. Run 'python3 run.py' to launch the review UI.")
        return

    # Launch pipeline in background process
    pipeline_proc = subprocess.Popen(
        [sys.executable, __file__, "--no-ui"],
        cwd=str(EVAL_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(f"[pipeline] Background pipeline started (PID {pipeline_proc.pid})")
    print("[pipeline] Transcripts + hooks will be generated while you review.\n")

    # Launch UI immediately (blocking)
    try:
        step_ui()
    finally:
        if pipeline_proc.poll() is None:
            pipeline_proc.terminate()
            print("[pipeline] Background pipeline stopped.")


if __name__ == "__main__":
    main()
