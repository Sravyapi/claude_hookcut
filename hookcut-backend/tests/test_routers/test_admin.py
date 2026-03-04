"""Tests for admin router — dashboard, users, rules, providers, audit logs."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.testclient import TestClient

from tests.conftest import (
    TEST_USER_ID, _make_app, TestSession, _cleanup,
    make_user, make_session, make_hook,
)
from app.dependencies import get_admin_user, get_db
from app.models.user import User
from app.models.admin import AdminAuditLog, PromptRule, ProviderConfig


# ─── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def admin_app():
    """FastAPI app with admin auth override — test user is admin."""
    application = _make_app(with_auth_override=True)

    # Override get_admin_user to return a fake admin User object
    async def override_get_admin_user():
        return User(
            id=TEST_USER_ID,
            email="admin@hookcut.com",
            role="admin",
            currency="USD",
            plan_tier="free",
        )

    application.dependency_overrides[get_admin_user] = override_get_admin_user
    return application


@pytest.fixture
def admin_client(admin_app):
    """HTTP test client authenticated as admin."""
    with TestClient(admin_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def nonadmin_app():
    """FastAPI app with non-admin auth — get_admin_user raises 403."""
    application = _make_app(with_auth_override=True)

    # Override get_admin_user to simulate a non-admin user hitting the endpoint
    async def override_get_admin_user():
        raise HTTPException(status_code=403, detail="Admin access required")

    application.dependency_overrides[get_admin_user] = override_get_admin_user
    return application


@pytest.fixture
def nonadmin_client(nonadmin_app):
    """HTTP test client authenticated as a non-admin user."""
    with TestClient(nonadmin_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def admin_db():
    """Database session for use alongside admin_client (separate session)."""
    session = TestSession()
    try:
        yield session
    finally:
        _cleanup(session)
        session.close()


# ─── GET /api/admin/dashboard ──────────────────────────────────────────────


class TestAdminDashboard:
    @patch("app.routers.admin.AdminService.get_dashboard_stats")
    def test_admin_gets_200(self, mock_stats, admin_client):
        mock_stats.return_value = {
            "total_users": 10,
            "total_sessions": 50,
            "total_shorts": 25,
            "active_subscriptions": 3,
            "recent_sessions": [],
        }

        resp = admin_client.get("/api/admin/dashboard")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_users"] == 10
        assert data["total_sessions"] == 50
        assert data["total_shorts"] == 25
        assert data["active_subscriptions"] == 3

    def test_non_admin_gets_403(self, nonadmin_client):
        """A non-admin user gets 403 from get_admin_user dependency."""
        resp = nonadmin_client.get("/api/admin/dashboard")
        assert resp.status_code == 403

    def test_unauthenticated_gets_401(self, unauthed_client):
        """No auth token at all triggers 401."""
        resp = unauthed_client.get("/api/admin/dashboard")

        assert resp.status_code == 401


# ─── GET /api/admin/users ─────────────────────────────────────────────────


class TestAdminUsers:
    @patch("app.routers.admin.AdminService.list_users")
    def test_returns_paginated_user_list(self, mock_list, admin_client):
        mock_list.return_value = {
            "users": [
                {
                    "id": "user-1",
                    "email": "user1@test.com",
                    "role": "user",
                    "plan_tier": "free",
                    "currency": "USD",
                    "created_at": "2024-01-01T00:00:00",
                    "session_count": 5,
                },
            ],
            "total": 1,
            "page": 1,
            "per_page": 20,
        }

        resp = admin_client.get("/api/admin/users")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["users"]) == 1
        assert data["users"][0]["email"] == "user1@test.com"
        assert data["page"] == 1

    @patch("app.routers.admin.AdminService.list_users")
    def test_pagination_params(self, mock_list, admin_client):
        mock_list.return_value = {
            "users": [],
            "total": 0,
            "page": 2,
            "per_page": 10,
        }

        resp = admin_client.get("/api/admin/users?page=2&per_page=10")

        assert resp.status_code == 200
        mock_list.assert_called_once()
        # Verify pagination params were passed
        call_args = mock_list.call_args
        assert call_args.kwargs.get("page", call_args.args[1] if len(call_args.args) > 1 else None) == 2


# ─── PATCH /api/admin/users/{id}/role ──────────────────────────────────────


class TestUpdateUserRole:
    @patch("app.routers.admin.AdminService.update_user_role")
    def test_role_change_works(self, mock_update, admin_client):
        mock_user = MagicMock()
        mock_user.id = "target-user"
        mock_user.email = "target@test.com"
        mock_user.role = "admin"
        mock_user.plan_tier = "free"
        mock_user.currency = "USD"
        mock_user.created_at = "2024-01-01T00:00:00"
        mock_user.session_count = 0
        mock_update.return_value = mock_user

        resp = admin_client.patch(
            "/api/admin/users/target-user/role",
            json={"role": "admin"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "admin"
        mock_update.assert_called_once()

    @patch("app.routers.admin.AdminService.update_user_role")
    def test_role_change_to_user(self, mock_update, admin_client):
        mock_user = MagicMock()
        mock_user.id = "target-user"
        mock_user.email = "target@test.com"
        mock_user.role = "user"
        mock_user.plan_tier = "free"
        mock_user.currency = "USD"
        mock_user.created_at = "2024-01-01T00:00:00"
        mock_user.session_count = 0
        mock_update.return_value = mock_user

        resp = admin_client.patch(
            "/api/admin/users/target-user/role",
            json={"role": "user"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "user"

    def test_invalid_role_rejected(self, admin_client):
        """Pydantic validation rejects roles that aren't 'user' or 'admin'."""
        resp = admin_client.patch(
            "/api/admin/users/target-user/role",
            json={"role": "superadmin"},
        )

        assert resp.status_code == 422


# ─── GET /api/admin/rules ─────────────────────────────────────────────────


class TestAdminRules:
    @patch("app.routers.admin.AdminService.list_rules")
    def test_returns_rule_list(self, mock_list, admin_client):
        from app.schemas.admin import PromptRuleListResponse, PromptRuleResponse
        mock_list.return_value = PromptRuleListResponse(
            rules=[PromptRuleResponse(
                id="rule-1", rule_key="A", version=1,
                title="One topic per hook",
                content="One topic per hook -- 3+ topics = FAIL",
                is_base_rule=True, is_active=True,
                created_at="2026-01-01T00:00:00",
            )]
        )

        resp = admin_client.get("/api/admin/rules")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["rules"]) == 1
        assert data["rules"][0]["rule_key"] == "A"


# ─── GET /api/admin/providers ─────────────────────────────────────────────


class TestAdminProviders:
    @patch("app.routers.admin.AdminService.list_providers")
    def test_returns_provider_list(self, mock_list, admin_client):
        from app.schemas.admin import ProviderListResponse, ProviderConfigResponse
        mock_list.return_value = ProviderListResponse(
            providers=[ProviderConfigResponse(
                provider_name="gemini", is_primary=True, is_fallback=False,
                is_enabled=True, model_id="gemini-2.5-flash",
                api_key_last4="ab12", api_key_set=True,
                updated_at="2026-01-01T00:00:00",
            )]
        )

        resp = admin_client.get("/api/admin/providers")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["providers"]) == 1
        assert data["providers"][0]["provider_name"] == "gemini"
        assert data["providers"][0]["is_primary"] is True


# ─── GET /api/admin/audit-logs ─────────────────────────────────────────────


class TestAdminAuditLogs:
    @patch("app.routers.admin.AdminService.list_audit_logs")
    def test_returns_audit_logs(self, mock_list, admin_client):
        mock_list.return_value = {
            "logs": [
                {
                    "id": "log-1",
                    "admin_email": "admin@hookcut.com",
                    "action": "role_changed",
                    "resource_type": "user",
                    "resource_id": "user-1",
                    "description": "Changed role from user to admin",
                    "before_state": {"role": "user"},
                    "after_state": {"role": "admin"},
                    "created_at": "2024-01-01T00:00:00",
                },
            ],
            "total": 1,
            "page": 1,
            "per_page": 20,
        }

        resp = admin_client.get("/api/admin/audit-logs")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["logs"]) == 1
        assert data["logs"][0]["action"] == "role_changed"
        assert data["logs"][0]["before_state"]["role"] == "user"
        assert data["logs"][0]["after_state"]["role"] == "admin"

    @patch("app.routers.admin.AdminService.list_audit_logs")
    def test_audit_logs_with_action_filter(self, mock_list, admin_client):
        mock_list.return_value = {
            "logs": [],
            "total": 0,
            "page": 1,
            "per_page": 20,
        }

        resp = admin_client.get("/api/admin/audit-logs?action=role_changed")

        assert resp.status_code == 200
        mock_list.assert_called_once()

    @patch("app.routers.admin.AdminService.list_audit_logs")
    def test_audit_logs_pagination(self, mock_list, admin_client):
        mock_list.return_value = {
            "logs": [],
            "total": 0,
            "page": 3,
            "per_page": 10,
        }

        resp = admin_client.get("/api/admin/audit-logs?page=3&per_page=10")

        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 3
        assert data["per_page"] == 10


# ─── Auth enforcement across endpoints ─────────────────────────────────────


class TestAdminAuthEnforcement:
    """Ensure non-admin and unauthenticated users are rejected on all endpoints."""

    ADMIN_ENDPOINTS = [
        ("GET", "/api/admin/dashboard"),
        ("GET", "/api/admin/users"),
        ("GET", "/api/admin/rules"),
        ("GET", "/api/admin/providers"),
        ("GET", "/api/admin/audit-logs"),
    ]

    def test_non_admin_rejected_on_all_endpoints(self, nonadmin_client):
        for method, path in self.ADMIN_ENDPOINTS:
            if method == "GET":
                resp = nonadmin_client.get(path)
            else:
                resp = nonadmin_client.post(path)
            assert resp.status_code == 403, f"Expected 403 for {method} {path}, got {resp.status_code}"

    def test_unauthenticated_rejected_on_all_endpoints(self, unauthed_client):
        for method, path in self.ADMIN_ENDPOINTS:
            if method == "GET":
                resp = unauthed_client.get(path)
            else:
                resp = unauthed_client.post(path)
            assert resp.status_code == 401, f"Expected 401 for {method} {path}, got {resp.status_code}"
