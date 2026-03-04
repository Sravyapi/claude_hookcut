"""Tests for user router endpoints."""
from tests.conftest import TEST_USER_ID, make_user, make_session


class TestGetBalance:
    def test_get_balance_default(self, client, db):
        """New user gets default 120 free minutes."""
        make_user(db, user_id=TEST_USER_ID)
        resp = client.get("/api/user/balance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["free_minutes_remaining"] == 120.0
        assert data["paid_minutes_remaining"] == 0.0
        assert data["payg_minutes_remaining"] == 0.0
        assert data["total_available"] == 120.0

    def test_get_balance_auto_creates_user(self, client):
        """Accessing balance auto-creates user via CreditManager."""
        resp = client.get("/api/user/balance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_available"] == 120.0


class TestGetHistory:
    def test_empty_history(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.get("/api/user/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sessions"] == []
        assert data["total"] == 0

    def test_history_with_sessions(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        for i in range(3):
            make_session(db, TEST_USER_ID, video_id=f"vid{i}")

        resp = client.get("/api/user/history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 3
        assert data["total"] == 3

    def test_history_pagination(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        for i in range(5):
            make_session(db, TEST_USER_ID, video_id=f"vid-p{i}")

        resp = client.get("/api/user/history?page=1&per_page=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2

    def test_history_returns_session_fields(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        make_session(db, TEST_USER_ID, status="completed")

        resp = client.get("/api/user/history")
        data = resp.json()
        session = data["sessions"][0]
        assert "video_title" in session
        assert "status" in session
        assert "minutes_charged" in session
        assert "created_at" in session


class TestGetProfile:
    def test_get_profile(self, client, db):
        make_user(db, user_id=TEST_USER_ID, email="profile@test.com", currency="USD")
        resp = client.get("/api/user/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == TEST_USER_ID
        assert data["email"] == "profile@test.com"
        assert data["currency"] == "USD"
        assert data["plan_tier"] == "free"

    def test_profile_not_found(self, client):
        resp = client.get("/api/user/profile")
        assert resp.status_code == 404


class TestUpdateCurrency:
    def test_update_to_inr(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.patch("/api/user/currency", json={"currency": "INR"})
        assert resp.status_code == 200
        assert resp.json()["currency"] == "INR"

    def test_update_to_usd(self, client, db):
        make_user(db, user_id=TEST_USER_ID, currency="INR")
        resp = client.patch("/api/user/currency", json={"currency": "USD"})
        assert resp.status_code == 200
        assert resp.json()["currency"] == "USD"

    def test_invalid_currency(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.patch("/api/user/currency", json={"currency": "EUR"})
        assert resp.status_code == 400

    def test_user_not_found(self, client):
        resp = client.patch("/api/user/currency", json={"currency": "INR"})
        assert resp.status_code == 404
