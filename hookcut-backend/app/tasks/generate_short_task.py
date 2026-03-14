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
from app.services.storage import get_storage_service
from app.utils import report_to_sentry
from app.services.transcript import TranscriptService

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
            logger.error(
                f"Short {short_id} not found in DB. "
                "This usually means the Celery task was dispatched before the DB transaction was committed."
            )
            return {"error": "Short not found"}

        session = db.get(AnalysisSession, short.session_id)
        if not session:
            logger.error(f"Session {short.session_id} not found for short {short_id}")
            short.status = "failed"
            short.error_message = "Parent session not found"
            db.commit()
            return {"error": "Session not found"}

        # For manual clips, hook is None
        hook = None
        if short.hook_id:
            hook = db.get(Hook, short.hook_id)
            if not hook:
                logger.error(f"Hook {short.hook_id} not found for short {short_id}")
                short.status = "failed"
                short.error_message = "Associated hook not found"
                db.commit()
                return {"error": "Hook not found"}

        generator = ShortGenerator()
        storage = get_storage_service()

        is_manual = short.source_type == "manual"

        # Use time overrides if set (from trim controls)
        start_sec = short.start_seconds_override
        end_sec = short.end_seconds_override

        if not is_manual and hook:
            # AI mode: use hook times with optional overrides
            start_sec = short.start_seconds_override if short.start_seconds_override is not None else hook.start_seconds
            end_sec = short.end_seconds_override if short.end_seconds_override is not None else hook.end_seconds

        def on_progress(status: str, pct: int, label: str):
            """Callback from generator to update DB status + Celery progress."""
            short.status = status
            db.commit()
            self.update_state(state="PROGRESS", meta={"stage": label, "progress": pct})

        # For manual clips, fetch video title if not already present
        if is_manual and not session.video_title:
            try:
                from app.services.video_metadata import VideoMetadataService
                meta = VideoMetadataService().fetch(session.video_id)
                if meta:
                    session.video_title = meta.title
                    session.video_duration_seconds = meta.duration_seconds
                    db.commit()
                    logger.info("Fetched video title for manual session %s: %s", session.id, meta.title)
            except Exception as e:
                logger.warning("Failed to fetch video title for manual clip: %s", e)

        # For manual clips, fetch transcript if not already present
        if is_manual and not session.transcript_text:
            on_progress("processing", 10, "Fetching transcript for captions...")
            try:
                ts = TranscriptService()
                transcript_result = ts.fetch(session.video_id, session.language or "English")
                if transcript_result:
                    session.transcript_text = transcript_result.text
                    db.commit()
                    logger.info("Fetched transcript for manual session %s (%d chars)", session.id, len(transcript_result.text))
            except Exception as e:
                logger.warning("Failed to fetch transcript for manual clip captions: %s", e)
                # Continue without captions rather than failing the whole clip

        work_dir = None
        try:
            # Shared params for both manual and AI-hook modes
            shared_params = dict(
                youtube_url=session.youtube_url,
                session_id=session.id,
                short_id=short.id,
                is_watermarked=short.is_watermarked,
                language=session.language,
                niche=session.niche,
                caption_style=short.caption_style or "clean",
                transcript_text=session.transcript_text or "",
                aspect_ratio=short.aspect_ratio or "9:16",
                audio_normalization=short.audio_normalization if short.audio_normalization is not None else True,
                interview_mode=session.interview_mode,
                speaker_count=session.speaker_count or 2,
                diarization_data=session.diarization_data,
                on_progress=on_progress,
            )

            if is_manual:
                result = generator.generate(
                    **shared_params,
                    hook=None,
                    captions_enabled=True,
                    source_type="manual",
                    start_seconds=start_sec,
                    end_seconds=end_sec,
                    video_title=session.video_title,
                )
            else:
                result = generator.generate(
                    **shared_params,
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
                )

            work_dir = Path(result.video_path).parent

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
            short.interview_layout = result.interview_layout
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
        finally:
            # Always clean up temp working directory, even on failure
            if work_dir and work_dir.exists():
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
                    _check_session_completion(db, session)
        except Exception as inner_err:
            logger.exception(f"Failed to mark short {short_id} as timed out: {inner_err}")
        return {"error": user_msg}
    except Exception as e:
        logger.exception(f"Short generation failed for {short_id}: {e}")
        report_to_sentry(e)
        try:
            short = db.get(Short, short_id)
            if short:
                short.status = "failed"
                short.error_message = str(e)[:ERROR_MSG_MAX_LEN]
                db.commit()

                session = db.get(AnalysisSession, short.session_id)
                if session:
                    _check_session_completion(db, session)
        except Exception as inner_err:
            logger.exception(f"Failed to mark short {short_id} as failed: {inner_err}")
        return {"error": str(e)}
    finally:
        db.close()


def _get_short_status_counts(db, session_id: str) -> dict[str, int]:
    """Return {status: count} for all shorts in a session — single query."""
    rows = db.execute(
        select(Short.status, func.count(Short.id))
        .where(Short.session_id == session_id)
        .group_by(Short.status)
    ).all()
    return {status: count for status, count in rows}


def _check_session_completion(db, session):
    """If all shorts are in a terminal state, update session accordingly.

    Terminal states: ready, failed, discarded.
    - If any short is "ready" → session "completed"
    - If all shorts failed → refund credits and mark session "failed"
    """
    counts = _get_short_status_counts(db, session.id)
    total = sum(counts.values())
    if total == 0:
        return

    terminal = counts.get("ready", 0) + counts.get("failed", 0) + counts.get("discarded", 0)
    if terminal < total:
        return  # Some shorts still in progress

    if counts.get("ready", 0) > 0:
        session.status = "completed"
        db.commit()
    else:
        # All terminal but none ready — all failed/discarded
        CreditManager(db).refund_and_fail(
            session.id,
            error_msg="All Short generations failed. Credits refunded.",
            _logger=logger,
        )
