"""Tests for analysis router — validate-url, analyze, hooks, regenerate, select-hooks."""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import select
from tests.conftest import TEST_USER_ID, make_user, make_session, make_hook
from app.models.user import CreditBalance


@pytest.fixture(autouse=True)
def no_rate_limit():
    """Disable rate limiting for all analysis router tests."""
    with patch("app.routers.analysis.rate_limiter.check"):
        yield


class TestValidateUrl:
    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_valid_url(self, mock_validate, mock_meta_cls, client):
        mock_validate.return_value = (True, "dQw4w9WgXcQ", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(
            title="Test Video", duration_seconds=300.0
        )
        mock_meta.validate_accessibility.return_value = (True, None)

        resp = client.post(
            "/api/validate-url",
            json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["video_id"] == "dQw4w9WgXcQ"
        assert data["title"] == "Test Video"

    @patch("app.services.analyze_service.validate_youtube_url")
    def test_invalid_url(self, mock_validate, client):
        mock_validate.return_value = (False, None, "Invalid YouTube URL")

        resp = client.post(
            "/api/validate-url",
            json={"youtube_url": "https://example.com/not-youtube"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert data["error"] == "Invalid YouTube URL"


class TestAnalyze:
    @patch("app.services.analyze_service.run_analysis")
    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_analyze_success(self, mock_validate, mock_meta_cls, mock_task, client, db):
        make_user(db, user_id=TEST_USER_ID)

        mock_validate.return_value = (True, "dQw4w9WgXcQ", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(
            title="Test Video", duration_seconds=300.0
        )
        mock_meta.validate_accessibility.return_value = (True, None)
        mock_task.delay.return_value = MagicMock(id="task-123")

        resp = client.post(
            "/api/analyze",
            json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                  "niche": "Generic", "language": "English"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == "task-123"
        assert data["video_title"] == "Test Video"
        assert data["minutes_charged"] == 5.0  # 300s / 60

    @patch("app.services.analyze_service.VideoMetadataService")
    @patch("app.services.analyze_service.validate_youtube_url")
    def test_analyze_insufficient_credits(self, mock_validate, mock_meta_cls, client, db):
        make_user(db, user_id=TEST_USER_ID)
        # Drain all credits
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == TEST_USER_ID)
        ).scalar_one_or_none()
        balance.free_minutes_remaining = 0.0
        db.commit()

        mock_validate.return_value = (True, "dQw4w9WgXcQ", None)
        mock_meta = mock_meta_cls.return_value
        mock_meta.fetch.return_value = MagicMock(
            title="Long Video", duration_seconds=600.0
        )
        mock_meta.validate_accessibility.return_value = (True, None)

        resp = client.post(
            "/api/analyze",
            json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                  "niche": "Generic", "language": "English"},
        )
        assert resp.status_code == 402

    @patch("app.services.analyze_service.validate_youtube_url")
    def test_analyze_invalid_url(self, mock_validate, client, db):
        make_user(db, user_id=TEST_USER_ID)
        mock_validate.return_value = (False, None, "Invalid URL")

        resp = client.post(
            "/api/analyze",
            json={"youtube_url": "bad-url", "niche": "Generic", "language": "English"},
        )
        assert resp.status_code == 400


class TestGetHooks:
    def test_get_hooks(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID)
        for i in range(5):
            make_hook(db, session.id, rank=i + 1, hook_text=f"Hook {i}")

        resp = client.get(f"/api/sessions/{session.id}/hooks")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == session.id
        assert len(data["hooks"]) == 5
        assert data["hooks"][0]["rank"] == 1

    def test_get_hooks_not_found(self, client):
        resp = client.get("/api/sessions/nonexistent/hooks")
        assert resp.status_code == 404

    def test_hooks_response_fields(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID)
        make_hook(db, session.id)

        resp = client.get(f"/api/sessions/{session.id}/hooks")
        hook = resp.json()["hooks"][0]
        assert "hook_text" in hook
        assert "scores" in hook
        assert "attention_score" in hook
        assert "hook_type" in hook
        assert "funnel_role" in hook


class TestRegenerate:
    @patch("app.services.analyze_service.run_analysis")
    def test_regenerate_hooks(self, mock_task, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="hooks_ready")
        make_hook(db, session.id)
        mock_task.delay.return_value = MagicMock(id="regen-task-1")

        resp = client.post(f"/api/sessions/{session.id}/regenerate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["regeneration_count"] == 1
        assert data["task_id"] == "regen-task-1"

    def test_regenerate_wrong_status(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="pending")

        resp = client.post(f"/api/sessions/{session.id}/regenerate")
        assert resp.status_code == 400

    def test_regenerate_not_found(self, client):
        resp = client.post("/api/sessions/nonexistent/regenerate")
        assert resp.status_code == 404


class TestSelectHooks:
    @patch("app.services.analyze_service.generate_short")
    def test_select_hooks(self, mock_task, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="hooks_ready")
        hook1 = make_hook(db, session.id, rank=1)
        hook2 = make_hook(db, session.id, rank=2, hook_text="Hook 2")
        mock_task.delay.return_value = MagicMock(id="short-task-1")

        resp = client.post(
            f"/api/sessions/{session.id}/select-hooks",
            json={"hook_ids": [hook1.id, hook2.id]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["short_ids"]) == 2

    def test_select_wrong_status(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="pending")

        resp = client.post(
            f"/api/sessions/{session.id}/select-hooks",
            json={"hook_ids": ["fake-id"]},
        )
        assert resp.status_code == 400

    def test_select_invalid_hook_id(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="hooks_ready")

        resp = client.post(
            f"/api/sessions/{session.id}/select-hooks",
            json={"hook_ids": ["nonexistent-hook"]},
        )
        assert resp.status_code == 400

    def test_select_too_many_hooks(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="hooks_ready")

        resp = client.post(
            f"/api/sessions/{session.id}/select-hooks",
            json={"hook_ids": ["a", "b", "c", "d"]},
        )
        assert resp.status_code == 422  # Pydantic validation
