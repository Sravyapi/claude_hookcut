import shutil
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from celery.exceptions import SoftTimeLimitExceeded
from app.tasks.celery_app import celery_app, ERROR_MSG_MAX_LEN, DOWNLOAD_URL_EXPIRES_SECONDS
from app.dependencies import get_db_session
from app.config import get_settings
from app.services.credit_manager import CreditManager
from app.models.session import AnalysisSession, Hook, Short
from app.services.short_generator import ShortGenerator
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=0, soft_time_limit=600, time_limit=660)
def generate_short(self, short_id: str):
    """
    Generate a single YouTube Short from a selected hook.
    Pipeline: yt-dlp segment → FFmpeg render → storage upload.
    """
    db = get_db_session()
    settings = get_settings()

    try:
        short = db.get(Short, short_id)
        if not short:
            logger.error(f"Short {short_id} not found")
            return {"error": "Short not found"}

        session = db.get(AnalysisSession, short.session_id)
        hook = db.get(Hook, short.hook_id)

        generator = ShortGenerator()
        storage = StorageService()

        # Use time overrides if set (from trim controls)
        start_sec = short.start_seconds_override if short.start_seconds_override is not None else hook.start_seconds
        end_sec = short.end_seconds_override if short.end_seconds_override is not None else hook.end_seconds

        def on_progress(status: str, pct: int, label: str):
            """Callback from generator to update DB status + Celery progress."""
            short.status = status
            db.commit()
            self.update_state(state="PROGRESS", meta={"stage": label, "progress": pct})

        result = generator.generate(
            youtube_url=session.youtube_url,
            hook={
                "start_time": hook.start_time,
                "end_time": hook.end_time,
                "start_seconds": start_sec,
                "end_seconds": end_sec,
                "hook_text": hook.hook_text,
                "is_composite": hook.is_composite,
                "hook_type": hook.hook_type or "",
                "attention_score": hook.attention_score or 0.0,
            },
            session_id=session.id,
            short_id=short.id,
            is_watermarked=short.is_watermarked,
            language=session.language,
            niche=session.niche,
            caption_style=short.caption_style or "clean",
            on_progress=on_progress,
        )

        # --- Step 3: Upload ---
        on_progress("uploading", 85, "Uploading...")

        video_key = f"shorts/{short.id}/video.mp4"
        thumb_key = f"shorts/{short.id}/thumbnail.jpg"

        # Upload video + thumbnail in parallel
        has_thumb = result.thumbnail_path and Path(result.thumbnail_path).exists()
        with ThreadPoolExecutor(max_workers=2) as executor:
            video_future = executor.submit(storage.upload, result.video_path, video_key)
            thumb_future = None
            if has_thumb:
                thumb_future = executor.submit(
                    storage.upload, result.thumbnail_path, thumb_key
                )
            video_future.result()
            if thumb_future:
                thumb_future.result()

        download_url = storage.get_download_url(video_key, expires_in=DOWNLOAD_URL_EXPIRES_SECONDS)

        # --- Finalize ---
        short.status = "ready"
        short.title = result.title
        short.cleaned_captions = result.cleaned_captions
        short.video_file_key = video_key
        short.thumbnail_file_key = thumb_key if has_thumb else None
        short.duration_seconds = result.duration_seconds
        short.file_size_bytes = result.file_size_bytes
        short.download_url = download_url
        short.download_url_expires_at = datetime.now(timezone.utc) + timedelta(seconds=DOWNLOAD_URL_EXPIRES_SECONDS)
        short.expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.TEMP_FILE_TTL_HOURS)
        db.commit()

        # Cleanup temp working directory
        work_dir = Path(result.video_path).parent
        shutil.rmtree(work_dir, ignore_errors=True)

        self.update_state(
            state="PROGRESS",
            meta={"stage": "Short ready!", "progress": 100},
        )

        # Check if all shorts for session are done
        _check_session_completion(db, session)

        return {
            "short_id": short.id,
            "status": "ready",
            "title": result.title,
            "duration": result.duration_seconds,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Short generation timed out for {short_id}")
        user_msg = "Short generation timed out after 10 minutes. Please try again."
        try:
            short = db.get(Short, short_id)
            if short:
                short.status = "failed"
                short.error_message = user_msg[:ERROR_MSG_MAX_LEN]
                db.commit()
                session = db.get(AnalysisSession, short.session_id)
                if session:
                    _check_all_shorts_failed(db, session)
        except Exception as inner_err:
            logger.exception(f"Failed to mark short {short_id} as timed out: {inner_err}")
        return {"error": user_msg}
    except Exception as e:
        logger.exception(f"Short generation failed for {short_id}: {e}")
        try:
            short = db.get(Short, short_id)
            if short:
                short.status = "failed"
                short.error_message = str(e)[:ERROR_MSG_MAX_LEN]
                db.commit()

                session = db.get(AnalysisSession, short.session_id)
                if session:
                    _check_all_shorts_failed(db, session)
        except Exception as inner_err:
            logger.exception(f"Failed to mark short {short_id} as failed: {inner_err}")
        return {"error": str(e)}
    finally:
        db.close()


def _get_short_status_counts(db, session_id: str) -> dict[str, int]:
    """Return {status: count} for all shorts in a session — single query."""
    from sqlalchemy import func
    rows = db.execute(
        select(Short.status, func.count(Short.id))
        .where(Short.session_id == session_id)
        .group_by(Short.status)
    ).all()
    return {status: count for status, count in rows}


def _check_session_completion(db, session):
    """If all shorts are ready, mark session completed."""
    counts = _get_short_status_counts(db, session.id)
    total = sum(counts.values())
    if total > 0 and counts.get("ready", 0) == total:
        session.status = "completed"
        db.commit()


def _check_all_shorts_failed(db, session):
    """If ALL shorts failed, refund credits and mark session as failed."""
    counts = _get_short_status_counts(db, session.id)
    total = sum(counts.values())
    if total > 0 and counts.get("failed", 0) == total:
        CreditManager(db).refund_and_fail(
            session.id,
            error_msg="All Short generations failed. Credits refunded.",
            _logger=logger,
        )
