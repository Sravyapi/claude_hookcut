"""
ShortsService — owns all Short retrieval and download business logic.

Routers call these static methods and convert HookCutError to HTTPException.
"""
import os
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.exceptions import ShortNotFoundError, ShortNotReadyError, InvalidStateError
from app.models.learning import LearningLog
from app.models.session import Short
from app.schemas.shorts import ShortResponse, ShortDownloadResponse
from app.services.storage import StorageService
from app.tasks.celery_app import DOWNLOAD_URL_EXPIRES_SECONDS

logger = logging.getLogger(__name__)


class ShortsService:

    @staticmethod
    def serve_local_file(file_key: str) -> tuple[str, str]:
        """
        Resolve a local storage path for serving (V0 only).

        Returns (absolute_file_path, media_type) tuple.
        Raises: InvalidStateError (R2 mode), ShortNotFoundError (file missing)
        """
        storage = StorageService()
        if storage.s3:
            raise InvalidStateError("Not available in R2 mode")
        path = storage._safe_local_path(file_key)
        if not os.path.exists(path):
            raise ShortNotFoundError("File not found")
        media_type = "video/mp4" if path.endswith(".mp4") else "image/jpeg"
        return path, media_type

    @staticmethod
    def get_short(db: Session, short_id: str) -> ShortResponse:
        """
        Get Short details including status and download URL.

        Raises: ShortNotFoundError
        """
        short = db.get(Short, short_id)
        if not short:
            raise ShortNotFoundError()

        thumbnail_url = None
        if short.thumbnail_file_key:
            storage = StorageService()
            thumbnail_url = storage.get_download_url(
                short.thumbnail_file_key, expires_in=DOWNLOAD_URL_EXPIRES_SECONDS
            )

        return ShortResponse(
            id=short.id,
            hook_id=short.hook_id,
            status=short.status,
            is_watermarked=short.is_watermarked,
            title=short.title,
            cleaned_captions=short.cleaned_captions,
            duration_seconds=short.duration_seconds,
            file_size_bytes=short.file_size_bytes,
            download_url=short.download_url,
            download_url_expires_at=short.download_url_expires_at,
            thumbnail_url=thumbnail_url,
            error_message=short.error_message,
        )

    @staticmethod
    def download_short(db: Session, short_id: str) -> ShortDownloadResponse:
        """
        Generate a fresh presigned download URL and log the download event.

        Raises: ShortNotFoundError, ShortNotReadyError, InvalidStateError
        """
        short = db.get(Short, short_id)
        if not short:
            raise ShortNotFoundError()

        if short.status != "ready":
            raise ShortNotReadyError(f"Short is not ready (status: {short.status})")

        if not short.video_file_key:
            raise InvalidStateError("No video file available")

        storage = StorageService()
        download_url = storage.get_download_url(
            short.video_file_key, expires_in=DOWNLOAD_URL_EXPIRES_SECONDS
        )
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=DOWNLOAD_URL_EXPIRES_SECONDS)

        short.download_url = download_url
        short.download_url_expires_at = expires_at

        # Log learning event (use relationship instead of separate query)
        if short.session:
            log_entry = LearningLog(
                session_id=short.session_id,
                event_type="short_downloaded",
                hook_id=short.hook_id,
                video_id=short.session.video_id,
                niche=short.session.niche,
                language=short.session.language,
                event_metadata={"is_watermarked": short.is_watermarked},
            )
            db.add(log_entry)

        db.commit()

        return ShortDownloadResponse(download_url=download_url, expires_at=expires_at)

    @staticmethod
    def discard_short(db: Session, short_id: str) -> dict:
        """
        Mark a Short as discarded (user chose not to download).

        Raises: ShortNotFoundError
        """
        short = db.get(Short, short_id)
        if not short:
            raise ShortNotFoundError()

        if short.session:
            log_entry = LearningLog(
                session_id=short.session_id,
                event_type="short_discarded",
                hook_id=short.hook_id,
                video_id=short.session.video_id,
                niche=short.session.niche,
                language=short.session.language,
            )
            db.add(log_entry)

        db.commit()
        return {"status": "discarded"}
