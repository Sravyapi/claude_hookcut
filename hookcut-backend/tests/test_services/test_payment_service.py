"""Tests for PaymentService — Stripe + Razorpay checkout creation (mocked)."""
import pytest
from unittest.mock import patch, MagicMock
from app.services.payment_service import PaymentService, PLAN_MINUTES, PLAN_PRICES, PAYG_RATES


class TestPaymentServiceRouting:
    def test_usd_routes_to_stripe(self):
        svc = PaymentService()
        with patch.object(svc, "_stripe_subscription") as mock:
            mock.return_value = MagicMock(checkout_url="https://stripe.com/checkout", session_id="sess_1")
            svc.create_subscription_checkout("u1", "u1@test.com", "lite", "USD")
            mock.assert_called_once_with("u1", "u1@test.com", "lite", "USD")

    def test_inr_routes_to_razorpay(self):
        svc = PaymentService()
        with patch.object(svc, "_razorpay_subscription") as mock:
            mock.return_value = MagicMock(checkout_url="https://rzp.io/checkout", session_id="sub_1")
            svc.create_subscription_checkout("u2", "u2@test.com", "pro", "INR")
            mock.assert_called_once_with("u2", "u2@test.com", "pro")

    def test_payg_usd_routes_to_stripe(self):
        svc = PaymentService()
        with patch.object(svc, "_stripe_payg") as mock:
            mock.return_value = MagicMock(checkout_url="url", session_id="cs_1")
            svc.create_payg_checkout("u3", "u3@test.com", 200, "USD")
            mock.assert_called_once_with("u3", "u3@test.com", 200, "USD")

    def test_payg_inr_routes_to_razorpay(self):
        svc = PaymentService()
        with patch.object(svc, "_razorpay_payg") as mock:
            mock.return_value = MagicMock(checkout_url="", session_id="order_1")
            svc.create_payg_checkout("u4", "u4@test.com", 100, "INR")
            mock.assert_called_once_with("u4", 100, "INR")


class TestPlanConstants:
    def test_plan_minutes(self):
        assert PLAN_MINUTES["lite"] == 100
        assert PLAN_MINUTES["pro"] == 500

    def test_plan_prices(self):
        assert PLAN_PRICES[("lite", "USD")] == 700
        assert PLAN_PRICES[("pro", "USD")] == 1300
        assert PLAN_PRICES[("lite", "INR")] == 49900
        assert PLAN_PRICES[("pro", "INR")] == 99900

    def test_payg_rates(self):
        assert PAYG_RATES["USD"] == 200
        assert PAYG_RATES["INR"] == 10000


class TestStripeCheckout:
    @patch("stripe.checkout.Session.create")
    @patch("stripe.api_key", new="sk_test_123")
    def test_stripe_subscription_checkout(self, mock_create):
        mock_create.return_value = MagicMock(url="https://checkout.stripe.com/pay/123", id="cs_abc")
        svc = PaymentService()
        with patch("app.services.payment_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                FEATURE_V0_MODE=False,
                STRIPE_SECRET_KEY="sk_test",
                FRONTEND_URL="http://localhost:3000",
            )
            result = svc._stripe_subscription("u1", "u1@test.com", "lite", "USD")
        assert result.provider == "stripe"
        assert result.checkout_url == "https://checkout.stripe.com/pay/123"

    @patch("stripe.checkout.Session.create")
    @patch("stripe.api_key", new="sk_test_123")
    def test_stripe_payg_checkout(self, mock_create):
        mock_create.return_value = MagicMock(url="https://checkout.stripe.com/pay/456", id="cs_def")
        svc = PaymentService()
        with patch("app.services.payment_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                FEATURE_V0_MODE=False,
                STRIPE_SECRET_KEY="sk_test",
                FRONTEND_URL="http://localhost:3000",
            )
            result = svc._stripe_payg("u2", "u2@test.com", 200, "USD")
        assert result.provider == "stripe"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["metadata"]["purchase_type"] == "payg"
        assert call_kwargs["metadata"]["minutes"] == "200"
