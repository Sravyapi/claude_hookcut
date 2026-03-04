"""Tests for JWT authentication middleware."""
import time
import jwt
import pytest

TEST_SECRET = "test-secret-for-jwt-signing-min-32chars!"


def _make_jwt(sub="user-123", exp_offset=3600, secret=TEST_SECRET):
    """Create a valid JWT token for testing."""
    payload = {
        "sub": sub,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_offset,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


class TestJWTAuth:
    def test_valid_token(self, unauthed_client):
        """Valid JWT returns user data (balance endpoint)."""
        token = _make_jwt(sub="auth-user-1")
        # Create user first via sync endpoint (no auth needed for this test path)
        # We test via the balance endpoint which requires auth
        resp = unauthed_client.get(
            "/api/user/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should get 200 (auto-creates user) or valid response
        assert resp.status_code == 200

    def test_missing_auth_header(self, unauthed_client):
        """No Authorization header returns 401."""
        resp = unauthed_client.get("/api/user/balance")
        assert resp.status_code == 401
        assert "Missing" in resp.json()["detail"]

    def test_invalid_auth_scheme(self, unauthed_client):
        """Non-Bearer scheme returns 401."""
        resp = unauthed_client.get(
            "/api/user/balance",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert resp.status_code == 401

    def test_expired_token(self, unauthed_client):
        """Expired JWT returns 401."""
        token = _make_jwt(exp_offset=-3600)  # Expired 1 hour ago
        resp = unauthed_client.get(
            "/api/user/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
        assert "expired" in resp.json()["detail"].lower()

    def test_invalid_token(self, unauthed_client):
        """Malformed JWT returns 401."""
        resp = unauthed_client.get(
            "/api/user/balance",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert resp.status_code == 401

    def test_wrong_secret(self, unauthed_client):
        """JWT signed with wrong secret returns 401."""
        token = _make_jwt(secret="wrong-secret-that-doesnt-match-backend")
        resp = unauthed_client.get(
            "/api/user/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    def test_missing_sub_claim(self, unauthed_client):
        """JWT without sub claim returns 401."""
        payload = {"iat": int(time.time()), "exp": int(time.time()) + 3600}
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        resp = unauthed_client.get(
            "/api/user/balance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
        assert "sub" in resp.json()["detail"].lower()
