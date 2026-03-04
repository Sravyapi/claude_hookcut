"""Tests for BillingService — billing/checkout business logic."""
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import select

from tests.conftest import make_user, TEST_USER_ID
from app.exceptions import InvalidStateError, UserNotFoundError, PaymentProcessingError
from app.models.user import CreditBalance
from app.services.billing_service import BillingService, PLANS_USD, PLANS_INR


class TestGetPlans:
    def test_returns_usd_plans_for_usd_user(self, db):
        make_user(db, user_id="bp1", currency="USD", plan_tier="free")
        result = BillingService.get_plans(db, "bp1")

        assert result.currency == "USD"
        assert result.current_tier == "free"
        assert len(result.plans) == 3
        assert result.plans == PLANS_USD

    def test_returns_inr_plans_for_inr_user(self, db):
        make_user(db, user_id="bp2", currency="INR", plan_tier="lite")
        result = BillingService.get_plans(db, "bp2")

        assert result.currency == "INR"
        assert result.current_tier == "lite"
        assert len(result.plans) == 3
        assert result.plans == PLANS_INR

    def test_defaults_to_usd_for_unknown_user(self, db):
        result = BillingService.get_plans(db, "nonexistent-user")

        assert result.currency == "USD"
        assert result.current_tier == "free"
        assert result.plans == PLANS_USD

    def test_plan_tiers_are_free_lite_pro(self, db):
        make_user(db, user_id="bp3")
        result = BillingService.get_plans(db, "bp3")
        tiers = [p.tier for p in result.plans]
        assert tiers == ["free", "lite", "pro"]


class TestCreateCheckout:
    @patch("app.services.billing_service.get_settings")
    def test_raises_in_v0_mode(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=True)
        make_user(db, user_id="cc1")

        with pytest.raises(InvalidStateError) as exc_info:
            BillingService.create_checkout(db, "cc1", "lite")
        assert "V0 mode" in exc_info.value.detail

    @patch("app.services.billing_service.get_settings")
    def test_raises_for_invalid_tier(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)
        make_user(db, user_id="cc2")

        with pytest.raises(InvalidStateError) as exc_info:
            BillingService.create_checkout(db, "cc2", "free")
        assert "Invalid plan tier" in exc_info.value.detail

    @patch("app.services.billing_service.get_settings")
    def test_raises_for_unknown_user(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)

        with pytest.raises(UserNotFoundError):
            BillingService.create_checkout(db, "nonexistent", "lite")

    @patch("app.services.billing_service.PaymentService")
    @patch("app.services.billing_service.get_settings")
    def test_success_returns_checkout_result(self, mock_settings, mock_payment_cls, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)
        mock_payment = MagicMock()
        mock_payment.create_subscription_checkout.return_value = MagicMock(
            checkout_url="https://pay.example.com/session/123",
            session_id="cs_123",
        )
        mock_payment_cls.return_value = mock_payment
        make_user(db, user_id="cc3", currency="USD")

        result = BillingService.create_checkout(db, "cc3", "pro")

        assert result.checkout_url == "https://pay.example.com/session/123"
        assert result.session_id == "cs_123"
        mock_payment.create_subscription_checkout.assert_called_once_with(
            user_id="cc3", email="cc3@test.com", plan_tier="pro", currency="USD",
        )

    @patch("app.services.billing_service.PaymentService")
    @patch("app.services.billing_service.get_settings")
    def test_payment_failure_raises_payment_processing_error(self, mock_settings, mock_payment_cls, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)
        mock_payment = MagicMock()
        mock_payment.create_subscription_checkout.side_effect = RuntimeError("Stripe down")
        mock_payment_cls.return_value = mock_payment
        make_user(db, user_id="cc4")

        with pytest.raises(PaymentProcessingError) as exc_info:
            BillingService.create_checkout(db, "cc4", "lite")
        assert "Failed to create checkout session" in exc_info.value.detail


class TestCreatePaygCheckout:
    @patch("app.services.billing_service.get_settings")
    def test_raises_in_v0_mode(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=True)
        make_user(db, user_id="pg1")

        with pytest.raises(InvalidStateError) as exc_info:
            BillingService.create_payg_checkout(db, "pg1", 100)
        assert "V0 mode" in exc_info.value.detail

    @patch("app.services.billing_service.get_settings")
    def test_raises_for_minutes_below_minimum(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)
        make_user(db, user_id="pg2")

        with pytest.raises(InvalidStateError) as exc_info:
            BillingService.create_payg_checkout(db, "pg2", 50)
        assert "multiple of 100" in exc_info.value.detail

    @patch("app.services.billing_service.get_settings")
    def test_raises_for_non_multiple_of_100(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)
        make_user(db, user_id="pg3")

        with pytest.raises(InvalidStateError) as exc_info:
            BillingService.create_payg_checkout(db, "pg3", 150)
        assert "multiple of 100" in exc_info.value.detail

    @patch("app.services.billing_service.get_settings")
    def test_raises_for_unknown_user(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)

        with pytest.raises(UserNotFoundError):
            BillingService.create_payg_checkout(db, "nonexistent", 100)

    @patch("app.services.billing_service.PaymentService")
    @patch("app.services.billing_service.get_settings")
    def test_success_returns_checkout_result(self, mock_settings, mock_payment_cls, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)
        mock_payment = MagicMock()
        mock_payment.create_payg_checkout.return_value = MagicMock(
            checkout_url="https://pay.example.com/payg/456",
            session_id="cs_456",
        )
        mock_payment_cls.return_value = mock_payment
        make_user(db, user_id="pg4", currency="INR")

        result = BillingService.create_payg_checkout(db, "pg4", 200)

        assert result.checkout_url == "https://pay.example.com/payg/456"
        assert result.session_id == "cs_456"
        mock_payment.create_payg_checkout.assert_called_once_with(
            user_id="pg4", email="pg4@test.com", minutes=200, currency="INR",
        )

    @patch("app.services.billing_service.PaymentService")
    @patch("app.services.billing_service.get_settings")
    def test_payment_failure_raises_payment_processing_error(self, mock_settings, mock_payment_cls, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)
        mock_payment = MagicMock()
        mock_payment.create_payg_checkout.side_effect = RuntimeError("Provider error")
        mock_payment_cls.return_value = mock_payment
        make_user(db, user_id="pg5")

        with pytest.raises(PaymentProcessingError) as exc_info:
            BillingService.create_payg_checkout(db, "pg5", 100)
        assert "Failed to create checkout session" in exc_info.value.detail


class TestSyncUser:
    @patch("app.services.billing_service.track_event")
    @patch("app.services.billing_service.identify_user")
    def test_creates_new_user(self, mock_identify, mock_track, db):
        result = BillingService.sync_user(db, "sync1", "sync1@example.com")

        assert result["user_id"] == "sync1"
        assert result["is_new"] is True
        assert result["plan_tier"] == "free"
        assert result["role"] == "user"

        # Verify user was actually created in DB
        from app.models.user import User
        user = db.get(User, "sync1")
        assert user is not None
        assert user.email == "sync1@example.com"

        # Verify credit balance was created
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "sync1")
        ).scalar_one_or_none()
        assert balance is not None
        assert balance.free_minutes_remaining == 120.0

        # Verify analytics calls
        mock_identify.assert_called_once_with("sync1", {"email": "sync1@example.com"})
        mock_track.assert_called_once_with("sync1", "user_signed_up", {"email": "sync1@example.com"})

    @patch("app.services.billing_service.track_event")
    @patch("app.services.billing_service.identify_user")
    def test_returns_existing_user(self, mock_identify, mock_track, db):
        make_user(db, user_id="sync2", plan_tier="pro")

        result = BillingService.sync_user(db, "sync2", "sync2@test.com")

        assert result["user_id"] == "sync2"
        assert result["is_new"] is False
        assert result["plan_tier"] == "pro"

        # Analytics should NOT be called for existing users
        mock_identify.assert_not_called()
        mock_track.assert_not_called()


class TestV0GrantCredits:
    @patch("app.services.billing_service.get_settings")
    def test_raises_when_v0_disabled(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=False)
        make_user(db, user_id="v0g1")

        with pytest.raises(InvalidStateError) as exc_info:
            BillingService.v0_grant_credits(db, "v0g1", paid_minutes=100.0, payg_minutes=0.0)
        assert "V0 mode" in exc_info.value.detail

    @patch("app.services.billing_service.get_settings")
    def test_grants_paid_minutes(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=True)
        make_user(db, user_id="v0g2")

        result = BillingService.v0_grant_credits(db, "v0g2", paid_minutes=200.0, payg_minutes=0.0)

        assert result["granted"]["paid_minutes"] == 200.0
        assert result["granted"]["payg_minutes"] == 0.0
        assert result["balance"]["paid"] == 200.0

    @patch("app.services.billing_service.get_settings")
    def test_grants_payg_minutes(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=True)
        make_user(db, user_id="v0g3")

        result = BillingService.v0_grant_credits(db, "v0g3", paid_minutes=0.0, payg_minutes=300.0)

        assert result["granted"]["payg_minutes"] == 300.0
        assert result["balance"]["payg"] == 300.0

    @patch("app.services.billing_service.get_settings")
    def test_grants_both_paid_and_payg(self, mock_settings, db):
        mock_settings.return_value = MagicMock(FEATURE_V0_MODE=True)
        make_user(db, user_id="v0g4")

        result = BillingService.v0_grant_credits(db, "v0g4", paid_minutes=100.0, payg_minutes=50.0)

        assert result["balance"]["paid"] == 100.0
        assert result["balance"]["payg"] == 50.0
        assert result["balance"]["free"] == 120.0  # default free minutes
        total = 100.0 + 50.0 + 120.0
        assert result["balance"]["total"] == total
