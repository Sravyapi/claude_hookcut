"""Tests for ClipService — manual clip generation."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import select

from app.models.session import AnalysisSession, Short
from app.models.user import CreditBalance
from app.schemas.clip import GenerateClipsRequest, ClipSegment
from app.services.clip_service import ClipService
from app.exceptions import InsufficientCreditsError, InvalidStateError, InvalidURLError
from tests.conftest import make_user, make_session, make_hook, make_short, TEST_USER_ID


def _make_request(
    clips=None,
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    caption_style="clean",
    aspect_ratio="9:16",
    ai_session_id=None,
):
    """Helper to create a GenerateClipsRequest."""
    if clips is None:
        clips = [ClipSegment(start_time=10.0, end_time=40.0)]
    return GenerateClipsRequest(
        youtube_url=url,
        clips=clips,
        caption_style=caption_style,
        aspect_ratio=aspect_ratio,
        ai_session_id=ai_session_id,
    )


class TestGenerateClipsHappyPath:
    """Happy path tests for manual clip generation."""

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_single_clip(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        user = make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        request = _make_request()
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert result.session_id
        assert len(result.task_ids) == 1
        assert result.total_duration_seconds == 30.0
        assert result.minutes_deducted == 0.0  # Pro = no deduction
        assert result.is_free_reclip is False

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_five_clips(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-x")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        clips = [ClipSegment(start_time=i * 30.0, end_time=(i + 1) * 30.0) for i in range(5)]
        request = _make_request(clips=clips)
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert len(result.task_ids) == 5
        assert result.total_duration_seconds == 150.0

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_ten_clips_max(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-x")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        clips = [ClipSegment(start_time=i * 10.0, end_time=i * 10.0 + 5.0) for i in range(10)]
        request = _make_request(clips=clips)
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert len(result.task_ids) == 10

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_session_created_with_manual_source(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        request = _make_request()
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        session = db.get(AnalysisSession, result.session_id)
        assert session.source_type == "manual"
        assert session.status == "generating_shorts"

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_shorts_created_with_correct_fields(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        request = _make_request(aspect_ratio="1:1", caption_style="bold")
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        session = db.get(AnalysisSession, result.session_id)
        shorts = session.shorts
        assert len(shorts) == 1
        assert shorts[0].hook_id is None
        assert shorts[0].source_type == "manual"
        assert shorts[0].aspect_ratio == "1:1"
        assert shorts[0].caption_style == "bold"
        assert shorts[0].start_seconds_override == 10.0
        assert shorts[0].end_seconds_override == 40.0


class TestValidation:
    """Request validation tests."""

    def test_invalid_url(self, db):
        make_user(db, user_id=TEST_USER_ID)
        request = _make_request(url="not-a-url")
        with pytest.raises((InvalidURLError, Exception)):
            ClipService.generate_clips(db, TEST_USER_ID, request)

    def test_more_than_10_clips_rejected_by_schema(self):
        with pytest.raises(ValueError, match="Maximum 10 clips"):
            _make_request(clips=[
                ClipSegment(start_time=i * 10.0, end_time=i * 10.0 + 5.0)
                for i in range(11)
            ])

    def test_clip_under_3_seconds_rejected_by_schema(self):
        with pytest.raises(ValueError, match="at least 3 seconds"):
            _make_request(clips=[ClipSegment(start_time=0.0, end_time=2.0)])

    def test_clip_beyond_2_hours_rejected_by_schema(self):
        with pytest.raises(ValueError, match="beyond 2 hours"):
            _make_request(clips=[ClipSegment(start_time=7100.0, end_time=7300.0)])

    def test_negative_time_rejected_by_schema(self):
        with pytest.raises(ValueError, match="non-negative"):
            ClipSegment(start_time=-1.0, end_time=5.0)

    def test_end_before_start_rejected_by_schema(self):
        with pytest.raises(ValueError, match="end_time must be after"):
            ClipSegment(start_time=10.0, end_time=5.0)

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_exceeding_10_clips_per_video_with_existing(self, mock_validate, mock_task, db):
        """10-clip limit counts existing clips for the same video."""
        mock_task.delay.return_value = MagicMock(id="task-x")
        user = make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        # Create a session with 8 existing shorts
        session = make_session(db, TEST_USER_ID, video_id="dQw4w9WgXcQ", source_type="manual")
        hook = make_hook(db, session.id)
        for _ in range(8):
            make_short(db, session.id, hook.id)

        # Try to add 3 more (8 + 3 = 11 > 10)
        clips = [ClipSegment(start_time=i * 10.0, end_time=i * 10.0 + 5.0) for i in range(3)]
        request = _make_request(clips=clips)

        with pytest.raises(InvalidStateError, match="Maximum"):
            ClipService.generate_clips(db, TEST_USER_ID, request)


class TestCreditDeduction:
    """Credit deduction tests for different plan tiers."""

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_pro_no_deduction(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        request = _make_request()
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert result.minutes_deducted == 0.0

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_pro_max_no_deduction(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro_max")

        request = _make_request()
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert result.minutes_deducted == 0.0

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_free_tier_always_allowed_watermarked(self, mock_validate, mock_task, db):
        """Free tier: clips always allowed, watermarked, no deduction."""
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="free")
        # No manual clip minutes needed — clips are always free

        request = _make_request()
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert result.minutes_deducted == 0.0
        session = db.get(AnalysisSession, result.session_id)
        assert session.is_watermarked is True


class TestFreeReclip:
    """Free re-clip from AI analysis tests."""

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_valid_ai_session_free_reclip(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="free")

        # Create a paid (non-watermarked) AI session for the same video
        ai_session = make_session(
            db, TEST_USER_ID, video_id="dQw4w9WgXcQ",
            status="completed", source_type="ai",
        )
        ai_session.is_watermarked = False  # Paid/PAYG AI analysis
        db.commit()

        request = _make_request(ai_session_id=ai_session.id)
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert result.is_free_reclip is True
        assert result.minutes_deducted == 0.0

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_expired_ai_session_not_free(self, mock_validate, mock_task, db):
        """AI session older than 24h should NOT qualify for free re-clip."""
        mock_task.delay.return_value = MagicMock(id="task-1")
        user = make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        # Create an old AI session
        ai_session = make_session(
            db, TEST_USER_ID, video_id="dQw4w9WgXcQ",
            status="completed", source_type="ai",
        )
        # Manually set created_at to >24h ago
        ai_session.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
        db.commit()

        request = _make_request(ai_session_id=ai_session.id)
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert result.is_free_reclip is False

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_wrong_users_session_not_free(self, mock_validate, mock_task, db):
        """Another user's AI session should NOT qualify."""
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")
        other_user = make_user(db, user_id="other-user", plan_tier="pro")

        ai_session = make_session(
            db, "other-user", video_id="dQw4w9WgXcQ",
            status="completed", source_type="ai",
        )

        request = _make_request(ai_session_id=ai_session.id)
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert result.is_free_reclip is False

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_wrong_video_not_free(self, mock_validate, mock_task, db):
        """AI session for different video should NOT qualify."""
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        ai_session = make_session(
            db, TEST_USER_ID, video_id="different_vid",
            status="completed", source_type="ai",
        )

        request = _make_request(ai_session_id=ai_session.id)
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        assert result.is_free_reclip is False


class TestAspectRatio:
    """Aspect ratio storage tests."""

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_9_16_default(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        request = _make_request()
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        session = db.get(AnalysisSession, result.session_id)
        assert session.shorts[0].aspect_ratio == "9:16"

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_1_1_square(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        request = _make_request(aspect_ratio="1:1")
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        session = db.get(AnalysisSession, result.session_id)
        assert session.shorts[0].aspect_ratio == "1:1"

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_4_5_portrait(self, mock_validate, mock_task, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        request = _make_request(aspect_ratio="4:5")
        result = ClipService.generate_clips(db, TEST_USER_ID, request)

        session = db.get(AnalysisSession, result.session_id)
        assert session.shorts[0].aspect_ratio == "4:5"
