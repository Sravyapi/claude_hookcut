"""Tests for tasks router — GET /api/tasks/{task_id} task polling."""
from unittest.mock import patch, MagicMock
from tests.conftest import TEST_USER_ID, make_user, make_session, make_short, make_hook
from app.models.session import AnalysisSession


def _set_task_id(db, session, task_id):
    """Attach a task_id to an existing session."""
    session.task_id = task_id
    db.commit()
    db.refresh(session)
    return session


class TestGetTaskStatus:
    def test_pending_task_returns_pending_status(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="pending")
        _set_task_id(db, session, "task-pending-1")

        with patch("app.tasks.celery_app.celery_app.AsyncResult") as mock_ar:
            mock_ar.return_value = MagicMock(
                status="PENDING", info=None, result=None
            )
            resp = client.get("/api/tasks/task-pending-1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == "task-pending-1"
        assert data["status"] == "PENDING"
        assert data["progress"] is None
        assert data["error"] is None

    def test_success_task_returns_result(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="hooks_ready")
        _set_task_id(db, session, "task-success-1")

        with patch("app.tasks.celery_app.celery_app.AsyncResult") as mock_ar:
            mock_ar.return_value = MagicMock(
                status="SUCCESS",
                result={"session_id": session.id},
                info=None,
            )
            resp = client.get("/api/tasks/task-success-1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert data["progress"] == 100
        assert data["result"] == {"session_id": session.id}

    def test_failure_task_returns_error(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="failed")
        _set_task_id(db, session, "task-failure-1")

        with patch("app.tasks.celery_app.celery_app.AsyncResult") as mock_ar:
            mock_ar.return_value = MagicMock(
                status="FAILURE",
                info=Exception("Something went wrong"),
                result=None,
            )
            resp = client.get("/api/tasks/task-failure-1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "FAILURE"
        assert data["error"] is not None
        assert "Something went wrong" in data["error"]

    def test_progress_task_returns_stage_and_progress(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="pending")
        _set_task_id(db, session, "task-progress-1")

        with patch("app.tasks.celery_app.celery_app.AsyncResult") as mock_ar:
            mock_ar.return_value = MagicMock(
                status="PROGRESS",
                info={"progress": 42, "stage": "transcribing"},
                result=None,
            )
            resp = client.get("/api/tasks/task-progress-1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PROGRESS"
        assert data["progress"] == 42
        assert data["stage"] == "transcribing"

    def test_task_not_found_returns_404(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        # No session or short with this task_id in DB
        resp = client.get("/api/tasks/task-nonexistent-xyz")
        assert resp.status_code == 404

    def test_unauthorized_returns_401(self, unauthed_client, db):
        resp = unauthed_client.get("/api/tasks/some-task-id")
        assert resp.status_code == 401

    def test_task_owned_by_short_returns_ok(self, client, db):
        """Task ownership can be verified via Short.task_id → AnalysisSession."""
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="hooks_ready")
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook_id=hook.id, status="processing")
        # Attach a task_id to the short
        short.task_id = "short-task-abc"
        db.commit()

        with patch("app.tasks.celery_app.celery_app.AsyncResult") as mock_ar:
            mock_ar.return_value = MagicMock(
                status="PENDING", info=None, result=None
            )
            resp = client.get("/api/tasks/short-task-abc")

        assert resp.status_code == 200
        assert resp.json()["task_id"] == "short-task-abc"

    def test_task_belonging_to_other_user_returns_403(self, client, db):
        """A task owned by another user should return 403."""
        make_user(db, user_id=TEST_USER_ID)
        other_user = make_user(db, user_id="other-user-999")
        session = make_session(db, "other-user-999", status="pending")
        _set_task_id(db, session, "other-user-task-1")

        resp = client.get("/api/tasks/other-user-task-1")
        assert resp.status_code == 403
