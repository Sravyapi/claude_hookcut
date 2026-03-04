"""Tests for billing router — plans, checkout, PAYG, v0-grant, user sync."""
from unittest.mock import patch, MagicMock
from tests.conftest import TEST_USER_ID, make_user
from app.models.user import CreditBalance


class TestGetPlans:
    def test_usd_plans(self, client, db):
        make_user(db, user_id=TEST_USER_ID, currency="USD")
        resp = client.get("/api/billing/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert data["currency"] == "USD"
        assert data["current_tier"] == "free"
        assert len(data["plans"]) == 3
        tiers = [p["tier"] for p in data["plans"]]
        assert tiers == ["free", "lite", "pro"]

    def test_inr_plans(self, client, db):
        make_user(db, user_id=TEST_USER_ID, currency="INR")
        resp = client.get("/api/billing/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert data["currency"] == "INR"
        assert "Rs" in data["plans"][1]["price_display"]

    def test_plans_shows_current_tier(self, client, db):
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")
        resp = client.get("/api/billing/plans")
        assert resp.json()["current_tier"] == "pro"


class TestCheckout:
    @patch("app.services.billing_service.PaymentService")
    def test_checkout_lite(self, mock_svc_cls, client, db):
        make_user(db, user_id=TEST_USER_ID)
        mock_svc = mock_svc_cls.return_value
        mock_svc.create_subscription_checkout.return_value = MagicMock(
            checkout_url="https://stripe.com/pay", session_id="cs_123"
        )
        resp = client.post("/api/billing/checkout?plan_tier=lite")
        assert resp.status_code == 200
        data = resp.json()
        assert data["checkout_url"] == "https://stripe.com/pay"
        assert data["session_id"] == "cs_123"

    def test_checkout_invalid_tier(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.post("/api/billing/checkout?plan_tier=mega")
        assert resp.status_code == 400

    def test_checkout_free_tier_rejected(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.post("/api/billing/checkout?plan_tier=free")
        assert resp.status_code == 400

    def test_checkout_user_not_found(self, client):
        resp = client.post("/api/billing/checkout?plan_tier=lite")
        assert resp.status_code == 404


class TestPayg:
    @patch("app.services.billing_service.PaymentService")
    def test_payg_purchase(self, mock_svc_cls, client, db):
        make_user(db, user_id=TEST_USER_ID)
        mock_svc = mock_svc_cls.return_value
        mock_svc.create_payg_checkout.return_value = MagicMock(
            checkout_url="https://stripe.com/pay", session_id="cs_456"
        )
        resp = client.post("/api/billing/payg?minutes=200")
        assert resp.status_code == 200
        data = resp.json()
        assert data["checkout_url"] == "https://stripe.com/pay"

    def test_payg_invalid_minutes(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.post("/api/billing/payg?minutes=50")
        assert resp.status_code == 400

    def test_payg_non_multiple_rejected(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        resp = client.post("/api/billing/payg?minutes=150")
        assert resp.status_code == 400


class TestV0Grant:
    def test_v0_grant_when_disabled(self, client, db):
        """V0 grant should fail when FEATURE_V0_MODE is False."""
        make_user(db, user_id=TEST_USER_ID)
        resp = client.post("/api/billing/v0-grant?paid_minutes=100")
        assert resp.status_code == 400

    @patch("app.services.billing_service.get_settings")
    def test_v0_grant_when_enabled(self, mock_settings, client, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=True)
        make_user(db, user_id=TEST_USER_ID)
        resp = client.post("/api/billing/v0-grant?paid_minutes=100&payg_minutes=50")
        assert resp.status_code == 200
        data = resp.json()
        assert data["granted"]["paid_minutes"] == 100
        assert data["granted"]["payg_minutes"] == 50


class TestSyncUser:
    def test_sync_new_user(self, client, db):
        resp = client.post("/api/auth/sync?email=new@test.com")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_new"] is True
        assert data["user_id"] == TEST_USER_ID

    def test_sync_existing_user(self, client, db):
        make_user(db, user_id=TEST_USER_ID, email="existing@test.com")
        resp = client.post("/api/auth/sync?email=existing@test.com")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_new"] is False
        assert data["plan_tier"] == "free"
