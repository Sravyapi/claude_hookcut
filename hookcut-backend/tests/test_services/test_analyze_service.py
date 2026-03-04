"""Tests for AnalyzeService — core analysis business logic."""
import pytest
from unittest.mock import patch, MagicMock

from sqlalchemy import select

from tests.conftest import TEST_USER_ID, make_user, make_session, make_hook
from app.services.analyze_service import AnalyzeService
from app.schemas.analysis import VideoValidateRequest
from app.models.session import AnalysisSession, Hook, Short
from app.models.user import CreditBalance
from app.exceptions import (
    InvalidURLError,
    MetadataFetchError,
    VideoAccessibilityError,
    InsufficientCreditsError,
    SessionNotFoundError,
    InvalidStateError,
    HooksNotReadyError,
)


# ─── validate_url ─────────────────────────────────────────────────────────


class TestValidateUrl:
    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_valid_youtube_url(self, mock_validate, mock_meta_cls):
        mock_validate.return_value = (True, "dQw4w9WgXcQ", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(
            title="Test Video", duration_seconds=300.0
        )
        mock_meta.validate_accessibility.return_value = (True, None)

        req = VideoValidateRequest(youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        result = AnalyzeService.validate_url(req)

        assert result.valid is True
        assert result.video_id == "dQw4w9WgXcQ"
        assert result.title == "Test Video"
        assert result.duration_seconds == 300.0
        assert result.error is None

    @patch("app.services.analyze_service.validate_youtube_url")
    def test_invalid_url(self, mock_validate):
        mock_validate.return_value = (False, None, "Invalid YouTube URL")

        req = VideoValidateRequest(youtube_url="not-a-url")
        result = AnalyzeService.validate_url(req)

        assert result.valid is False
        assert result.error == "Invalid YouTube URL"
        assert result.video_id is None

    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_non_youtube_url(self, mock_validate, mock_meta_cls):
        mock_validate.return_value = (False, None, "Not a YouTube URL")

        req = VideoValidateRequest(youtube_url="https://vimeo.com/123456")
        result = AnalyzeService.validate_url(req)

        assert result.valid is False
        assert "Not a YouTube URL" in result.error

    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_metadata_fetch_fails(self, mock_validate, mock_meta_cls):
        mock_validate.return_value = (True, "abc123", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = None

        req = VideoValidateRequest(youtube_url="https://www.youtube.com/watch?v=abc123")
        result = AnalyzeService.validate_url(req)

        assert result.valid is False
        assert "metadata" in result.error.lower()

    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_video_not_accessible(self, mock_validate, mock_meta_cls):
        mock_validate.return_value = (True, "abc123", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(title="Private Video", duration_seconds=60.0)
        mock_meta.validate_accessibility.return_value = (False, "Video is private")

        req = VideoValidateRequest(youtube_url="https://www.youtube.com/watch?v=abc123")
        result = AnalyzeService.validate_url(req)

        assert result.valid is False
        assert result.error == "Video is private"


# ─── start_analysis ───────────────────────────────────────────────────────


class TestStartAnalysis:
    @patch("app.services.analyze_service.track")
    @patch("app.services.analyze_service.run_analysis")
    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_successful_start(self, mock_validate, mock_meta_cls, mock_task, mock_track, db):
        make_user(db, user_id="sa1")

        mock_validate.return_value = (True, "dQw4w9WgXcQ", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(title="Test Video", duration_seconds=300.0)
        mock_meta.validate_accessibility.return_value = (True, None)
        mock_task.delay.return_value = MagicMock(id="task-abc")

        result = AnalyzeService.start_analysis(
            db, "sa1", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "Generic", "English"
        )

        assert result["task_id"] == "task-abc"
        assert result["video_title"] == "Test Video"
        assert result["minutes_charged"] == 5.0  # 300s / 60
        assert result["session_id"] is not None
        mock_task.delay.assert_called_once()
        mock_track.assert_called_once()

    @patch("app.services.analyze_service.validate_youtube_url")
    def test_invalid_url_raises(self, mock_validate, db):
        make_user(db, user_id="sa2")
        mock_validate.return_value = (False, None, "Bad URL")

        with pytest.raises(InvalidURLError):
            AnalyzeService.start_analysis(
                db, "sa2", "bad-url", "Generic", "English"
            )

    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_metadata_fetch_failure(self, mock_validate, mock_meta_cls, db):
        make_user(db, user_id="sa3")
        mock_validate.return_value = (True, "abc123", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = None

        with pytest.raises(MetadataFetchError):
            AnalyzeService.start_analysis(
                db, "sa3", "https://www.youtube.com/watch?v=abc123", "Generic", "English"
            )

    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_video_not_accessible_raises(self, mock_validate, mock_meta_cls, db):
        make_user(db, user_id="sa4")
        mock_validate.return_value = (True, "abc123", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(title="Private", duration_seconds=60.0)
        mock_meta.validate_accessibility.return_value = (False, "Video is private")

        with pytest.raises(VideoAccessibilityError):
            AnalyzeService.start_analysis(
                db, "sa4", "https://www.youtube.com/watch?v=abc123", "Generic", "English"
            )

    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_insufficient_credits(self, mock_validate, mock_meta_cls, db):
        make_user(db, user_id="sa5")
        # Drain all credits
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "sa5")
        ).scalar_one_or_none()
        balance.free_minutes_remaining = 0.0
        db.commit()

        mock_validate.return_value = (True, "abc123", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(title="Long Video", duration_seconds=600.0)
        mock_meta.validate_accessibility.return_value = (True, None)

        with pytest.raises(InsufficientCreditsError):
            AnalyzeService.start_analysis(
                db, "sa5", "https://www.youtube.com/watch?v=abc123", "Generic", "English"
            )

    @patch("app.services.analyze_service.track")
    @patch("app.services.analyze_service.run_analysis")
    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_auto_creates_user(self, mock_validate, mock_meta_cls, mock_task, mock_track, db):
        """start_analysis auto-creates user via _ensure_user if missing."""
        mock_validate.return_value = (True, "dQw4w9WgXcQ", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(title="Test", duration_seconds=120.0)
        mock_meta.validate_accessibility.return_value = (True, None)
        mock_task.delay.return_value = MagicMock(id="task-new")

        result = AnalyzeService.start_analysis(
            db, "brand-new-user", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "Generic", "English"
        )

        assert result["session_id"] is not None
        # Verify user and balance were auto-created
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "brand-new-user")
        ).scalar_one_or_none()
        assert balance is not None

    @patch("app.services.analyze_service.track")
    @patch("app.services.analyze_service.run_analysis")
    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_session_created_in_db(self, mock_validate, mock_meta_cls, mock_task, mock_track, db):
        make_user(db, user_id="sa6")
        mock_validate.return_value = (True, "dQw4w9WgXcQ", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(title="DB Test", duration_seconds=180.0)
        mock_meta.validate_accessibility.return_value = (True, None)
        mock_task.delay.return_value = MagicMock(id="task-db")

        result = AnalyzeService.start_analysis(
            db, "sa6", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "Generic", "English"
        )

        session = db.get(AnalysisSession, result["session_id"])
        assert session is not None
        assert session.user_id == "sa6"
        assert session.video_id == "dQw4w9WgXcQ"
        assert session.task_id == "task-db"


# ─── get_hooks ─────────────────────────────────────────────────────────────


class TestGetHooks:
    def test_session_with_hooks(self, db):
        make_user(db, user_id="gh1")
        session = make_session(db, "gh1", status="hooks_ready")
        for i in range(5):
            make_hook(db, session.id, rank=i + 1, hook_text=f"Hook {i}")

        result = AnalyzeService.get_hooks(db, session.id)

        assert result["session"].id == session.id
        assert len(result["hooks"]) == 5
        assert result["hooks"][0].rank == 1

    def test_session_not_found(self, db):
        with pytest.raises(SessionNotFoundError):
            AnalyzeService.get_hooks(db, "nonexistent-session-id")

    def test_session_still_processing(self, db):
        """get_hooks returns session even when still processing (no hooks yet)."""
        make_user(db, user_id="gh3")
        session = make_session(db, "gh3", status="pending")

        result = AnalyzeService.get_hooks(db, session.id)

        assert result["session"].id == session.id
        assert result["session"].status == "pending"
        assert len(result["hooks"]) == 0

    def test_hooks_ordered_by_rank(self, db):
        make_user(db, user_id="gh4")
        session = make_session(db, "gh4")
        # Create hooks in reverse order
        make_hook(db, session.id, rank=3, hook_text="Third")
        make_hook(db, session.id, rank=1, hook_text="First")
        make_hook(db, session.id, rank=2, hook_text="Second")

        result = AnalyzeService.get_hooks(db, session.id)

        assert result["hooks"][0].rank == 1
        assert result["hooks"][1].rank == 2
        assert result["hooks"][2].rank == 3


# ─── regenerate_hooks ─────────────────────────────────────────────────────


class TestRegenerateHooks:
    @patch("app.services.analyze_service.run_analysis")
    def test_successful_regeneration(self, mock_task, db):
        make_user(db, user_id="rg1")
        session = make_session(db, "rg1", status="hooks_ready")
        make_hook(db, session.id)
        mock_task.delay.return_value = MagicMock(id="regen-task-1")

        result = AnalyzeService.regenerate_hooks(db, session.id)

        assert result["session_id"] == session.id
        assert result["task_id"] == "regen-task-1"
        assert result["regeneration_count"] == 1
        assert result["fee_charged"] is None  # First regen is free
        mock_task.delay.assert_called_once_with(session.id)

    @patch("app.services.analyze_service.run_analysis")
    def test_second_regeneration_charges_fee(self, mock_task, db):
        make_user(db, user_id="rg2")
        session = make_session(db, "rg2", status="hooks_ready")
        session.regeneration_count = 1  # Already regenerated once
        db.commit()
        make_hook(db, session.id)
        mock_task.delay.return_value = MagicMock(id="regen-task-2")

        result = AnalyzeService.regenerate_hooks(db, session.id)

        assert result["regeneration_count"] == 2
        assert result["fee_charged"] is not None
        assert result["currency"] is not None

    def test_session_not_found(self, db):
        with pytest.raises(SessionNotFoundError):
            AnalyzeService.regenerate_hooks(db, "nonexistent-session-id")

    def test_wrong_status_raises(self, db):
        make_user(db, user_id="rg4")
        session = make_session(db, "rg4", status="pending")

        with pytest.raises(InvalidStateError):
            AnalyzeService.regenerate_hooks(db, session.id)

    @patch("app.services.analyze_service.run_analysis")
    def test_completed_status_allowed(self, mock_task, db):
        """Regeneration is allowed from 'completed' status too."""
        make_user(db, user_id="rg5")
        session = make_session(db, "rg5", status="completed")
        make_hook(db, session.id)
        mock_task.delay.return_value = MagicMock(id="regen-task-5")

        result = AnalyzeService.regenerate_hooks(db, session.id)

        assert result["regeneration_count"] == 1


# ─── select_hooks ──────────────────────────────────────────────────────────


class TestSelectHooks:
    @patch("app.services.analyze_service.generate_short")
    def test_valid_selection(self, mock_task, db):
        make_user(db, user_id="sh1")
        session = make_session(db, "sh1", status="hooks_ready")
        hook1 = make_hook(db, session.id, rank=1, hook_text="Hook 1")
        hook2 = make_hook(db, session.id, rank=2, hook_text="Hook 2")
        mock_task.delay.return_value = MagicMock(id="short-task-1")

        result = AnalyzeService.select_hooks(
            db, session.id, [hook1.id, hook2.id], "clean", {}
        )

        assert len(result["short_ids"]) == 2
        assert len(result["task_ids"]) == 2
        # Verify session status changed
        db.refresh(session)
        assert session.status == "generating_shorts"

    @patch("app.services.analyze_service.generate_short")
    def test_single_hook_selection(self, mock_task, db):
        make_user(db, user_id="sh2")
        session = make_session(db, "sh2", status="hooks_ready")
        hook = make_hook(db, session.id, rank=1)
        mock_task.delay.return_value = MagicMock(id="short-task-2")

        result = AnalyzeService.select_hooks(
            db, session.id, [hook.id], "clean", {}
        )

        assert len(result["short_ids"]) == 1

    def test_session_not_found(self, db):
        with pytest.raises(SessionNotFoundError):
            AnalyzeService.select_hooks(
                db, "nonexistent", ["fake-hook"], "clean", {}
            )

    def test_invalid_hook_ids(self, db):
        make_user(db, user_id="sh4")
        session = make_session(db, "sh4", status="hooks_ready")
        make_hook(db, session.id)  # Create one real hook

        with pytest.raises(InvalidStateError, match="not found in this session"):
            AnalyzeService.select_hooks(
                db, session.id, ["nonexistent-hook-id"], "clean", {}
            )

    def test_wrong_status_raises(self, db):
        make_user(db, user_id="sh5")
        session = make_session(db, "sh5", status="pending")

        with pytest.raises(HooksNotReadyError):
            AnalyzeService.select_hooks(
                db, session.id, ["any-hook"], "clean", {}
            )

    @patch("app.services.analyze_service.generate_short")
    def test_short_records_created_in_db(self, mock_task, db):
        make_user(db, user_id="sh6")
        session = make_session(db, "sh6", status="hooks_ready")
        hook = make_hook(db, session.id, rank=1)
        mock_task.delay.return_value = MagicMock(id="short-task-6")

        result = AnalyzeService.select_hooks(
            db, session.id, [hook.id], "bold", {}
        )

        short = db.get(Short, result["short_ids"][0])
        assert short is not None
        assert short.session_id == session.id
        assert short.hook_id == hook.id
        assert short.caption_style == "bold"
        assert short.status == "queued"

    @patch("app.services.analyze_service.generate_short")
    def test_hooks_marked_selected(self, mock_task, db):
        make_user(db, user_id="sh7")
        session = make_session(db, "sh7", status="hooks_ready")
        hook1 = make_hook(db, session.id, rank=1, hook_text="Selected")
        hook2 = make_hook(db, session.id, rank=2, hook_text="Not selected")
        mock_task.delay.return_value = MagicMock(id="short-task-7")

        AnalyzeService.select_hooks(
            db, session.id, [hook1.id], "clean", {}
        )

        db.refresh(hook1)
        db.refresh(hook2)
        assert hook1.is_selected is True
        assert hook2.is_selected is not True
