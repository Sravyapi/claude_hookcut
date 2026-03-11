"""Tests for manual clip credit behavior (via ClipService).

New model:
- Watermarked clips are always free for everyone (no deduction).
- Pro/Pro Max get watermark-free clips at no cost.
- Users who did a paid/PAYG AI analysis on a video get watermark-free clips (free re-clip).
- All other users get watermarked clips (free).
"""
import pytest
from datetime import datetime, timezone, timedelta
from tests.conftest import TEST_USER_ID, make_user
from app.services.clip_service import ClipService
from app.models.session import AnalysisSession
from app.schemas.clip import GenerateClipsRequest, ClipSegment
from unittest.mock import patch, MagicMock


def _make_ai_session(db, user_id: str, video_id: str, is_watermarked: bool = False, hours_ago: int = 1):
    """Helper: insert a completed AI analysis session."""
    session = AnalysisSession(
        user_id=user_id,
        youtube_url=f"https://www.youtube.com/watch?v={video_id}",
        video_id=video_id,
        video_title="Test",
        video_duration_seconds=300.0,
        niche="Tech",
        language="English",
        status="completed",
        source_type="ai",
        is_watermarked=is_watermarked,
        created_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class TestManualClipWatermarkLogic:

    @patch("app.services.clip_service.generate_short")
    def test_free_user_gets_watermarked_clips(self, mock_task, db):
        """Free users always get watermarked clips (free, no deduction)."""
        make_user(db, user_id=TEST_USER_ID, plan_tier="free")
        mock_task.delay.return_value = MagicMock(id="task-1")

        with patch("app.services.clip_service.validate_youtube_url", return_value=(True, "abc123", None)):
            req = GenerateClipsRequest(
                youtube_url="https://www.youtube.com/watch?v=abc123",
                clips=[ClipSegment(start_time=0, end_time=30)],
            )
            resp = ClipService.generate_clips(db, TEST_USER_ID, req)

        session = db.get(AnalysisSession, resp.session_id)
        assert session.is_watermarked is True
        assert session.minutes_charged == 0.0

    @patch("app.services.clip_service.generate_short")
    def test_pro_user_gets_watermark_free_clips(self, mock_task, db):
        """Pro users always get watermark-free clips."""
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")
        mock_task.delay.return_value = MagicMock(id="task-1")

        with patch("app.services.clip_service.validate_youtube_url", return_value=(True, "abc123", None)):
            req = GenerateClipsRequest(
                youtube_url="https://www.youtube.com/watch?v=abc123",
                clips=[ClipSegment(start_time=0, end_time=30)],
            )
            resp = ClipService.generate_clips(db, TEST_USER_ID, req)

        session = db.get(AnalysisSession, resp.session_id)
        assert session.is_watermarked is False
        assert session.minutes_charged == 0.0

    @patch("app.services.clip_service.generate_short")
    def test_free_reclip_from_paid_ai_session_is_watermark_free(self, mock_task, db):
        """Clip on a paid-analyzed video is watermark-free (free re-clip)."""
        make_user(db, user_id=TEST_USER_ID, plan_tier="free")
        ai_session = _make_ai_session(db, TEST_USER_ID, "abc123", is_watermarked=False)
        mock_task.delay.return_value = MagicMock(id="task-1")

        with patch("app.services.clip_service.validate_youtube_url", return_value=(True, "abc123", None)):
            req = GenerateClipsRequest(
                youtube_url="https://www.youtube.com/watch?v=abc123",
                clips=[ClipSegment(start_time=0, end_time=30)],
                ai_session_id=ai_session.id,
            )
            resp = ClipService.generate_clips(db, TEST_USER_ID, req)

        session = db.get(AnalysisSession, resp.session_id)
        assert session.is_watermarked is False
        assert resp.is_free_reclip is True

    @patch("app.services.clip_service.generate_short")
    def test_free_reclip_from_free_ai_session_is_watermarked(self, mock_task, db):
        """Clip on a free (watermarked) AI session does NOT qualify as free re-clip."""
        make_user(db, user_id=TEST_USER_ID, plan_tier="free")
        ai_session = _make_ai_session(db, TEST_USER_ID, "abc123", is_watermarked=True)
        mock_task.delay.return_value = MagicMock(id="task-1")

        with patch("app.services.clip_service.validate_youtube_url", return_value=(True, "abc123", None)):
            req = GenerateClipsRequest(
                youtube_url="https://www.youtube.com/watch?v=abc123",
                clips=[ClipSegment(start_time=0, end_time=30)],
                ai_session_id=ai_session.id,
            )
            resp = ClipService.generate_clips(db, TEST_USER_ID, req)

        session = db.get(AnalysisSession, resp.session_id)
        assert session.is_watermarked is True
        assert resp.is_free_reclip is False
