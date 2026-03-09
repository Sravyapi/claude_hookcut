"""Tests for scheduled Celery tasks."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import select

from app.models.session import AnalysisSession
from tests.conftest import make_user, make_session, TEST_USER_ID


class TestCleanupStuckSessions:
    """Test the cleanup_stuck_sessions scheduled task."""

    def test_marks_stuck_analyzing_as_failed(self, db):
        user = make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, user.id, status="analyzing")
        session_id = session.id
        # Backdate created_at to simulate stuck session
        session.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()

        from app.tasks.scheduled import cleanup_stuck_sessions
        with patch("app.tasks.scheduled._acquire_task_lock", return_value=(True, None)):
            with patch("app.tasks.scheduled.get_db_session", return_value=db):
                result = cleanup_stuck_sessions()

        assert result["recovered"] == 1
        refreshed = db.get(AnalysisSession, session_id)
        assert refreshed.status == "failed"
        assert "timed out" in refreshed.error_message

    def test_ignores_recent_sessions(self, db):
        user = make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, user.id, status="analyzing")
        session_id = session.id

        from app.tasks.scheduled import cleanup_stuck_sessions
        with patch("app.tasks.scheduled._acquire_task_lock", return_value=(True, None)):
            with patch("app.tasks.scheduled.get_db_session", return_value=db):
                result = cleanup_stuck_sessions()

        assert result["recovered"] == 0
        refreshed = db.get(AnalysisSession, session_id)
        assert refreshed.status == "analyzing"

    def test_ignores_completed_sessions(self, db):
        user = make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, user.id, status="completed")
        session_id = session.id
        session.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()

        from app.tasks.scheduled import cleanup_stuck_sessions
        with patch("app.tasks.scheduled._acquire_task_lock", return_value=(True, None)):
            with patch("app.tasks.scheduled.get_db_session", return_value=db):
                result = cleanup_stuck_sessions()

        assert result["recovered"] == 0
        refreshed = db.get(AnalysisSession, session_id)
        assert refreshed.status == "completed"

    def test_skips_when_lock_held(self, db):
        from app.tasks.scheduled import cleanup_stuck_sessions
        with patch("app.tasks.scheduled._acquire_task_lock", return_value=(False, None)):
            result = cleanup_stuck_sessions()

        assert result["skipped"] is True
