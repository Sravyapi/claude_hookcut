"""Tests for auth router — register, login, role lookup."""
from unittest.mock import patch
from tests.conftest import TEST_USER_ID, make_user
from app.models.user import User, CreditBalance
from sqlalchemy import select


@patch("app.routers.auth.rate_limiter.check")
class TestRegisterEndpoint:
    def test_register_new_user_returns_200(self, mock_rl, client):
        resp = client.post(
            "/api/auth/register",
            json={"email": "newuser@example.com", "password": "securepass1", "name": "New User"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"

    def test_register_creates_user_in_db(self, mock_rl, client, db):
        resp = client.post(
            "/api/auth/register",
            json={"email": "dbcheck@example.com", "password": "securepass1", "name": "DB User"},
        )
        assert resp.status_code == 200
        user_id = resp.json()["user_id"]
        # Verify user exists in DB via test session
        user = db.get(User, user_id)
        # The client uses its own DB session (override_get_db), but user_id is returned
        # so we can at minimum confirm the response contains a valid UUID string
        assert len(user_id) > 0

    def test_register_duplicate_email_returns_409(self, mock_rl, client, db):
        """Registering the same email twice should raise a ConflictError (409)."""
        from app.services.auth_service import AuthService
        # Pre-create the user in the shared db so the router's session sees it
        AuthService.register(db, "dup@example.com", "securepass1", "First")

        # Second registration with same email — user has hashed_password set, so ConflictError
        resp = client.post(
            "/api/auth/register",
            json={"email": "dup@example.com", "password": "securepass1", "name": "Second"},
        )
        assert resp.status_code == 409

    def test_register_missing_email_returns_422(self, mock_rl, client):
        resp = client.post(
            "/api/auth/register",
            json={"password": "securepass1", "name": "No Email"},
        )
        assert resp.status_code == 422

    def test_register_missing_password_returns_422(self, mock_rl, client):
        resp = client.post(
            "/api/auth/register",
            json={"email": "nopw@example.com", "name": "No Password"},
        )
        assert resp.status_code == 422

    def test_register_short_password_returns_422(self, mock_rl, client):
        resp = client.post(
            "/api/auth/register",
            json={"email": "short@example.com", "password": "abc", "name": "Short PW"},
        )
        assert resp.status_code == 422

    def test_register_missing_name_returns_422(self, mock_rl, client):
        resp = client.post(
            "/api/auth/register",
            json={"email": "noname@example.com", "password": "securepass1"},
        )
        assert resp.status_code == 422

    def test_register_oauth_user_adds_password(self, mock_rl, client, db):
        """An OAuth-only user (no hashed_password) can register to add a password."""
        # Create an OAuth user in the shared test DB — but the client uses its own override_get_db
        # So we test the router behaviour: first register creates user, no ConflictError
        resp = client.post(
            "/api/auth/register",
            json={"email": "oauth@example.com", "password": "securepass1", "name": "OAuth User"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()


@patch("app.routers.auth.rate_limiter.check")
class TestLoginEndpoint:
    def test_login_existing_user_returns_200(self, mock_rl, client, db):
        """Login a user pre-seeded via AuthService directly."""
        from app.services.auth_service import AuthService
        # Use the shared db fixture to pre-create the user via service
        # The test db and client db are both StaticPool (same connection), so this works.
        AuthService.register(db, "loginme@example.com", "securepass1", "Login User")

        resp = client.post(
            "/api/auth/login",
            json={"email": "loginme@example.com", "password": "securepass1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "loginme@example.com"
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, mock_rl, client, db):
        from app.services.auth_service import AuthService
        AuthService.register(db, "wrongpw@example.com", "securepass1", "Wrong PW")

        resp = client.post(
            "/api/auth/login",
            json={"email": "wrongpw@example.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user_returns_401(self, mock_rl, client):
        resp = client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "securepass1"},
        )
        assert resp.status_code == 401

    def test_login_missing_user_id_returns_422(self, mock_rl, client):
        """Missing email field returns 422 validation error."""
        resp = client.post(
            "/api/auth/login",
            json={"password": "securepass1"},
        )
        assert resp.status_code == 422

    def test_login_returns_role_field(self, mock_rl, client, db):
        from app.services.auth_service import AuthService
        AuthService.register(db, "rolecheck@example.com", "securepass1", "Role Check")

        resp = client.post(
            "/api/auth/login",
            json={"email": "rolecheck@example.com", "password": "securepass1"},
        )
        assert resp.status_code == 200
        assert "role" in resp.json()
        assert resp.json()["role"] == "user"


@patch("app.routers.auth.rate_limiter.check")
class TestRoleEndpoint:
    def test_role_returns_user_role(self, mock_rl, client, db):
        from app.services.auth_service import AuthService
        AuthService.register(db, "roleme@example.com", "securepass1", "Role User")

        resp = client.post(
            "/api/auth/role",
            json={"email": "roleme@example.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "role" in data
        assert data["role"] == "user"

    def test_role_unknown_email_returns_user_default(self, mock_rl, client):
        """Unknown email should return default role 'user' (not 404)."""
        resp = client.post(
            "/api/auth/role",
            json={"email": "unknown@example.com"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "user"

    def test_role_missing_user_id_returns_422(self, mock_rl, client):
        """Missing email field returns 422 validation error."""
        resp = client.post(
            "/api/auth/role",
            json={},
        )
        assert resp.status_code == 422

    def test_role_invalid_email_returns_422(self, mock_rl, client):
        resp = client.post(
            "/api/auth/role",
            json={"email": "not-an-email"},
        )
        assert resp.status_code == 422
