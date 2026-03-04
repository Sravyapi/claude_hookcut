import shutil
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime, timedelta, timezone
from app.tasks.celery_app import celery_app, ERROR_MSG_MAX_LEN, DOWNLOAD_URL_EXPIRES_SECONDS
from app.dependencies import get_db_session
from app.config import get_settings
from app.services.credit_manager import CreditManager

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=0)
def generate_short(self, short_id: str):
    """
    Generate a single YouTube Short from a selected hook.
    Pipeline: yt-dlp segment → FFmpeg render → storage upload.
    """
    db = get_db_session()
    settings = get_settings()

    try:
        from app.models.session import AnalysisSession, Hook, Short
        from app.services.short_generator import ShortGenerator
        from app.services.storage import StorageService

        short = db.get(Short, short_id)
        if not short:
            logger.error(f"Short {short_id} not found")
            return {"error": "Short not found"}

        session = db.get(AnalysisSession, short.session_id)
        hook = db.get(Hook, short.hook_id)

        # --- Step 1: Download + Process ---
        short.status = "processing"
        db.commit()
        self.update_state(
            state="PROGRESS",
            meta={"stage": "Generating Short...", "progress": 10},
        )

        generator = ShortGenerator()
        storage = StorageService()

        # Use time overrides if set (from trim controls)
        start_sec = short.start_seconds_override if short.start_seconds_override is not None else hook.start_seconds
        end_sec = short.end_seconds_override if short.end_seconds_override is not None else hook.end_seconds

        result = generator.generate(
            youtube_url=session.youtube_url,
            hook={
                "start_time": hook.start_time,
                "end_time": hook.end_time,
                "start_seconds": start_sec,
                "end_seconds": end_sec,
                "hook_text": hook.hook_text,
                "is_composite": hook.is_composite,
            },
            session_id=session.id,
            short_id=short.id,
            is_watermarked=short.is_watermarked,
            language=session.language,
            niche=session.niche,
            caption_style=short.caption_style or "clean",
        )

        # --- Step 2: Upload + Finalize ---
        self.update_state(
            state="PROGRESS",
            meta={"stage": "Saving Short...", "progress": 80},
        )

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


def _check_session_completion(db, session):
    """If all shorts are ready, mark session completed."""
    from sqlalchemy import func, select
    from app.models.session import Short

    total = db.execute(select(func.count(Short.id)).where(Short.session_id == session.id)).scalar()
    ready = db.execute(select(func.count(Short.id)).where(Short.session_id == session.id, Short.status == "ready")).scalar()
    if total > 0 and total == ready:
        session.status = "completed"
        db.commit()


def _check_all_shorts_failed(db, session):
    """If ALL shorts failed, refund credits and mark session as failed."""
    from sqlalchemy import func, select
    from app.models.session import Short

    total = db.execute(select(func.count(Short.id)).where(Short.session_id == session.id)).scalar()
    failed = db.execute(select(func.count(Short.id)).where(Short.session_id == session.id, Short.status == "failed")).scalar()
    if total > 0 and total == failed:
        CreditManager(db).refund_and_fail(
            session.id,
            error_msg="All Short generations failed. Credits refunded.",
            _logger=logger,
        )
