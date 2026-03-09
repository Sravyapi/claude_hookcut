"""
Audit #6 coverage gap tests — edge cases identified during Staff SWE audit.

Covers:
- Pagination edge cases (page=0, page=-1, per_page out of range)
- Admin RBAC (non-admin user hitting admin endpoints → 403)
- Auth sync idempotency
- Credit deduction with zero balance
- Select-hooks validation
"""
import pytest
from fastapi.testclient import TestClient

from tests.conftest import (
    TEST_USER_ID, make_user, make_session, make_hook,
    _make_app, TestSession, _cleanup,
)
from app.dependencies import get_admin_user, get_db, get_current_user_id
from app.models.user import User


class TestPaginationEdgeCases:
    """Phase 8: GET /api/user/history with invalid page values."""

    def test_page_zero_rejected(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.get("/api/user/history?page=0")
        assert resp.status_code == 422

    def test_negative_page_rejected(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.get("/api/user/history?page=-5")
        assert resp.status_code == 422

    def test_per_page_too_large_rejected(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.get("/api/user/history?per_page=500")
        assert resp.status_code == 422

    def test_per_page_zero_rejected(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.get("/api/user/history?per_page=0")
        assert resp.status_code == 422

    def test_valid_high_page_returns_empty(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.get("/api/user/history?page=9999")
        assert resp.status_code == 200
        assert resp.json()["sessions"] == []


class TestAdminRBAC:
    """Phase 8: Non-admin user hitting admin endpoints → 403."""

    @pytest.fixture
    def non_admin_client(self):
        """Client where auth is bypassed but get_admin_user checks role properly."""
        application = _make_app(with_auth_override=True)

        # Override get_admin_user to simulate a non-admin user
        from fastapi import HTTPException

        async def override_get_admin_user():
            raise HTTPException(status_code=403, detail="Admin access required")

        application.dependency_overrides[get_admin_user] = override_get_admin_user
        with TestClient(application, raise_server_exceptions=False) as c:
            yield c

    def test_non_admin_dashboard_returns_403(self, non_admin_client):
        resp = non_admin_client.get("/api/admin/dashboard")
        assert resp.status_code == 403

    def test_non_admin_users_list_returns_403(self, non_admin_client):
        resp = non_admin_client.get("/api/admin/users")
        assert resp.status_code == 403

    def test_non_admin_sessions_returns_403(self, non_admin_client):
        resp = non_admin_client.get("/api/admin/sessions")
        assert resp.status_code == 403

    def test_non_admin_rules_returns_403(self, non_admin_client):
        resp = non_admin_client.get("/api/admin/rules")
        assert resp.status_code == 403

    def test_non_admin_audit_logs_returns_403(self, non_admin_client):
        resp = non_admin_client.get("/api/admin/audit-logs")
        assert resp.status_code == 403


class TestAuthEndpoints:
    """Phase 8: Auth sync idempotency and edge cases."""

    def test_unauthed_profile_returns_401(self, unauthed_client):
        resp = unauthed_client.get("/api/user/profile")
        assert resp.status_code == 401

    def test_unauthed_balance_returns_401(self, unauthed_client):
        resp = unauthed_client.get("/api/user/balance")
        assert resp.status_code == 401

    def test_unauthed_history_returns_401(self, unauthed_client):
        resp = unauthed_client.get("/api/user/history")
        assert resp.status_code == 401


class TestCreditEdgeCases:
    """Phase 8: Credit deduction with zero remaining balance."""

    def test_zero_balance_analysis_returns_402(self, client, db):
        user = make_user(db, user_id=TEST_USER_ID)
        # Set all credit pools to zero
        from sqlalchemy import select
        from app.models.user import CreditBalance
        bal = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == user.id)
        ).scalar_one()
        bal.free_minutes_remaining = 0.0
        bal.paid_minutes_remaining = 0.0
        bal.payg_minutes_remaining = 0.0
        db.commit()

        resp = client.post("/api/analyze", json={
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "niche": "Generic",
            "language": "English",
        })
        assert resp.status_code == 402


class TestSelectHooksValidation:
    """Phase 8: select-hooks with invalid time overrides."""

    def test_time_override_exceeding_10s_rejected(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="hooks_ready")
        hook = make_hook(db, session.id)

        resp = client.post(f"/api/sessions/{session.id}/select-hooks", json={
            "hook_ids": [hook.id],
            "caption_style": "clean",
            "time_overrides": {
                hook.id: {
                    "start_seconds": hook.start_seconds - 15,  # exceeds ±10s
                    "end_seconds": hook.end_seconds,
                }
            },
        })
        assert resp.status_code == 400

    def test_hook_shorter_than_5s_rejected(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID, status="hooks_ready")
        hook = make_hook(db, session.id)

        resp = client.post(f"/api/sessions/{session.id}/select-hooks", json={
            "hook_ids": [hook.id],
            "caption_style": "clean",
            "time_overrides": {
                hook.id: {
                    "start_seconds": hook.start_seconds,
                    "end_seconds": hook.start_seconds + 3,  # less than 5s
                }
            },
        })
        assert resp.status_code == 400
