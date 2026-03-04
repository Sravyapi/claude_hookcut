"""Tests for ShortsService — Short retrieval and download business logic."""
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import select

from tests.conftest import make_user, make_session, make_hook, make_short
from app.exceptions import ShortNotFoundError, ShortNotReadyError, InvalidStateError
from app.models.learning import LearningLog
from app.services.shorts_service import ShortsService


class TestGetShort:
    def test_returns_short_details(self, db):
        user = make_user(db, user_id="gs1")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        short.title = "Test Short Title"
        short.is_watermarked = True
        short.duration_seconds = 28.5
        db.commit()

        with patch("app.services.shorts_service.StorageService") as mock_storage_cls:
            mock_storage = MagicMock()
            mock_storage_cls.return_value = mock_storage

            result = ShortsService.get_short(db, short.id)

        assert result.id == short.id
        assert result.hook_id == hook.id
        assert result.status == "ready"
        assert result.is_watermarked is True
        assert result.title == "Test Short Title"
        assert result.duration_seconds == 28.5

    def test_raises_for_nonexistent_short(self, db):
        with pytest.raises(ShortNotFoundError):
            ShortsService.get_short(db, "nonexistent-short-id")

    @patch("app.services.shorts_service.StorageService")
    def test_includes_thumbnail_url_when_present(self, mock_storage_cls, db):
        user = make_user(db, user_id="gs2")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        short.thumbnail_file_key = "shorts/gs2/thumb.jpg"
        db.commit()

        mock_storage = MagicMock()
        mock_storage.get_download_url.return_value = "https://cdn.example.com/thumb.jpg"
        mock_storage_cls.return_value = mock_storage

        result = ShortsService.get_short(db, short.id)

        assert result.thumbnail_url == "https://cdn.example.com/thumb.jpg"
        mock_storage.get_download_url.assert_called_once_with(
            "shorts/gs2/thumb.jpg", expires_in=3600,
        )

    def test_thumbnail_url_is_none_without_key(self, db):
        user = make_user(db, user_id="gs3")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="queued")
        # thumbnail_file_key is None by default

        with patch("app.services.shorts_service.StorageService"):
            result = ShortsService.get_short(db, short.id)

        assert result.thumbnail_url is None


class TestDownloadShort:
    @patch("app.services.shorts_service.StorageService")
    def test_generates_download_url_for_ready_short(self, mock_storage_cls, db):
        user = make_user(db, user_id="ds1")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        short.video_file_key = "shorts/ds1/video.mp4"
        db.commit()

        mock_storage = MagicMock()
        mock_storage.get_download_url.return_value = "https://cdn.example.com/video.mp4?sig=abc"
        mock_storage_cls.return_value = mock_storage

        result = ShortsService.download_short(db, short.id)

        assert result.download_url == "https://cdn.example.com/video.mp4?sig=abc"
        assert result.expires_at is not None
        mock_storage.get_download_url.assert_called_once_with(
            "shorts/ds1/video.mp4", expires_in=3600,
        )

    def test_raises_for_nonexistent_short(self, db):
        with pytest.raises(ShortNotFoundError):
            ShortsService.download_short(db, "nonexistent-short-id")

    def test_raises_for_not_ready_short(self, db):
        user = make_user(db, user_id="ds2")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="processing")

        with pytest.raises(ShortNotReadyError) as exc_info:
            ShortsService.download_short(db, short.id)
        assert "processing" in exc_info.value.detail

    def test_raises_for_ready_short_without_file(self, db):
        user = make_user(db, user_id="ds3")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        # video_file_key is None by default

        with pytest.raises(InvalidStateError) as exc_info:
            ShortsService.download_short(db, short.id)
        assert "No video file" in exc_info.value.detail

    @patch("app.services.shorts_service.StorageService")
    def test_updates_short_download_url_in_db(self, mock_storage_cls, db):
        user = make_user(db, user_id="ds4")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        short.video_file_key = "shorts/ds4/video.mp4"
        db.commit()

        mock_storage = MagicMock()
        mock_storage.get_download_url.return_value = "https://cdn.example.com/video.mp4"
        mock_storage_cls.return_value = mock_storage

        ShortsService.download_short(db, short.id)

        db.refresh(short)
        assert short.download_url == "https://cdn.example.com/video.mp4"
        assert short.download_url_expires_at is not None

    @patch("app.services.shorts_service.StorageService")
    def test_creates_learning_log_entry(self, mock_storage_cls, db):
        user = make_user(db, user_id="ds5")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        short.video_file_key = "shorts/ds5/video.mp4"
        db.commit()

        mock_storage = MagicMock()
        mock_storage.get_download_url.return_value = "https://cdn.example.com/video.mp4"
        mock_storage_cls.return_value = mock_storage

        ShortsService.download_short(db, short.id)

        log = db.execute(
            select(LearningLog).where(
                LearningLog.session_id == session.id,
                LearningLog.event_type == "short_downloaded",
            )
        ).scalar_one_or_none()
        assert log is not None
        assert log.hook_id == hook.id
        assert log.video_id == session.video_id
        assert log.niche == session.niche


class TestDiscardShort:
    def test_returns_discarded_status(self, db):
        user = make_user(db, user_id="disc1")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")

        result = ShortsService.discard_short(db, short.id)

        assert result == {"status": "discarded"}

    def test_raises_for_nonexistent_short(self, db):
        with pytest.raises(ShortNotFoundError):
            ShortsService.discard_short(db, "nonexistent-short-id")

    def test_creates_learning_log_entry(self, db):
        user = make_user(db, user_id="disc2")
        session = make_session(db, user.id)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")

        ShortsService.discard_short(db, short.id)

        log = db.execute(
            select(LearningLog).where(
                LearningLog.session_id == session.id,
                LearningLog.event_type == "short_discarded",
            )
        ).scalar_one_or_none()
        assert log is not None
        assert log.hook_id == hook.id
        assert log.video_id == session.video_id
