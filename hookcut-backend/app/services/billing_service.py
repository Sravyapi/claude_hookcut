"""
BillingService — owns all billing/checkout business logic.

Routers call these static methods and convert HookCutError to HTTPException.
"""
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import UserNotFoundError, InvalidStateError, PaymentProcessingError
from app.models.user import User, CreditBalance
from app.schemas.billing import PlanInfo, PlansResponse
from app.services.analytics import track as track_event, identify as identify_user
from app.services.credit_manager import CreditManager
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


def _ensure_payments_enabled() -> None:
    """Guard: raise InvalidStateError if V0 mode is active (payments disabled)."""
    if get_settings().FEATURE_V0_MODE:
        raise InvalidStateError(
            "Payment processing not available in V0 mode. "
            "Use /api/billing/v0-grant to add test credits."
        )


PLANS_INR = [
    PlanInfo(tier="free", price_display="Free", watermark_free_minutes=0, currency="INR"),
    PlanInfo(tier="lite", price_display="Rs 499/mo", watermark_free_minutes=100, currency="INR"),
    PlanInfo(tier="pro", price_display="Rs 999/mo", watermark_free_minutes=500, currency="INR"),
]

PLANS_USD = [
    PlanInfo(tier="free", price_display="Free", watermark_free_minutes=0, currency="USD"),
    PlanInfo(tier="lite", price_display="$7/mo", watermark_free_minutes=100, currency="USD"),
    PlanInfo(tier="pro", price_display="$13/mo", watermark_free_minutes=500, currency="USD"),
]


@dataclass
class CheckoutResult:
    checkout_url: str
    session_id: str


class BillingService:

    @staticmethod
    def get_plans(db: Session, user_id: str) -> PlansResponse:
        """Get available subscription plans for user's currency."""
        user = db.get(User, user_id)
        currency = user.currency if user else "USD"
        plans = PLANS_INR if currency == "INR" else PLANS_USD

        return PlansResponse(
            current_tier=user.plan_tier if user else "free",
            currency=currency,
            plans=plans,
        )

    @staticmethod
    def create_checkout(db: Session, user_id: str, plan_tier: str) -> CheckoutResult:
        """
        Create a checkout session for subscription purchase.

        Raises: InvalidStateError (V0 mode or bad tier), UserNotFoundError, PaymentProcessingError
        """
        _ensure_payments_enabled()

        if plan_tier not in ("lite", "pro"):
            raise InvalidStateError("Invalid plan tier. Must be 'lite' or 'pro'")

        user = db.get(User, user_id)
        if not user:
            raise UserNotFoundError()

        payment_svc = PaymentService()
        try:
            result = payment_svc.create_subscription_checkout(
                user_id=user_id,
                email=user.email,
                plan_tier=plan_tier,
                currency=user.currency,
            )
        except Exception as e:
            logger.error(f"Checkout creation failed: {e}")
            raise PaymentProcessingError("Failed to create checkout session")

        return CheckoutResult(checkout_url=result.checkout_url, session_id=result.session_id)

    @staticmethod
    def create_payg_checkout(db: Session, user_id: str, minutes: int) -> CheckoutResult:
        """
        Create a PAYG checkout session.

        Raises: InvalidStateError (V0 mode or bad minutes), UserNotFoundError, PaymentProcessingError
        """
        _ensure_payments_enabled()

        if minutes < 100 or minutes % 100 != 0:
            raise InvalidStateError("Minutes must be a multiple of 100 (minimum 100)")

        user = db.get(User, user_id)
        if not user:
            raise UserNotFoundError()

        payment_svc = PaymentService()
        try:
            result = payment_svc.create_payg_checkout(
                user_id=user_id,
                email=user.email,
                minutes=minutes,
                currency=user.currency,
            )
        except Exception as e:
            logger.error(f"PAYG checkout creation failed: {e}")
            raise PaymentProcessingError("Failed to create checkout session")

        return CheckoutResult(checkout_url=result.checkout_url, session_id=result.session_id)

    @staticmethod
    def sync_user(db: Session, user_id: str, email: str) -> dict:
        """
        Ensure user exists in backend after NextAuth login.
        Returns dict with user_id, is_new, plan_tier, role.
        """
        user = db.get(User, user_id)
        is_new = False

        if not user:
            user = User(id=user_id, email=email, currency="USD")
            db.add(user)
            db.flush()

            balance = CreditBalance(user_id=user_id)
            db.add(balance)
            db.commit()
            is_new = True

        if is_new:
            identify_user(user_id, {"email": email})
            track_event(user_id, "user_signed_up", {"email": email})

        return {
            "user_id": user_id,
            "is_new": is_new,
            "plan_tier": user.plan_tier,
            "role": user.role,
        }

    @staticmethod
    def v0_grant_credits(db: Session, user_id: str, paid_minutes: float, payg_minutes: float) -> dict:
        """
        V0 only: Grant test credits without payment.

        Raises: InvalidStateError (not V0 mode)
        """
        if not get_settings().FEATURE_V0_MODE:
            raise InvalidStateError("Only available in V0 mode")

        credit_mgr = CreditManager(db)

        if paid_minutes > 0:
            credit_mgr.add_paid_minutes(
                user_id, paid_minutes, provider="v0_test", provider_ref="v0_grant"
            )
        if payg_minutes > 0:
            credit_mgr.add_payg_minutes(
                user_id, payg_minutes,
                amount=0, currency="USD", provider="v0_test", provider_ref="v0_grant",
            )

        balance = credit_mgr.get_balance(user_id)
        return {
            "granted": {"paid_minutes": paid_minutes, "payg_minutes": payg_minutes},
            "balance": {
                "paid": balance.paid_minutes_remaining,
                "payg": balance.payg_minutes_remaining,
                "free": balance.free_minutes_remaining,
                "total": balance.total_available,
            },
        }

    @staticmethod
    def handle_stripe_webhook(db: Session, payload: bytes, signature: str) -> dict:
        """
        Verify Stripe webhook signature and dispatch to appropriate handler.

        Raises: InvalidStateError (bad signature)
        """
        import stripe
        settings = get_settings()
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            raise InvalidStateError("Invalid webhook signature")

        from app.services.webhook_service import WebhookService

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            return WebhookService.handle_stripe_checkout_completed(db, data)
        elif event_type == "invoice.paid":
            return WebhookService.handle_stripe_invoice_paid(db, data)
        elif event_type == "customer.subscription.deleted":
            return WebhookService.handle_stripe_subscription_deleted(db, data)

        return {"status": "ok"}

    @staticmethod
    def handle_razorpay_webhook(db: Session, payload: bytes, signature: str) -> dict:
        """
        Verify Razorpay webhook signature and dispatch to appropriate handler.

        Raises: InvalidStateError (bad signature)
        """
        import razorpay
        import json
        settings = get_settings()

        try:
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            client.utility.verify_webhook_signature(
                payload.decode(), signature, settings.RAZORPAY_WEBHOOK_SECRET
            )
        except Exception as e:
            logger.warning(f"Razorpay signature verification failed: {e}")
            raise InvalidStateError("Invalid webhook signature")

        from app.services.webhook_service import WebhookService

        body = json.loads(payload)
        event_type = body.get("event", "")
        entity = BillingService._extract_razorpay_entity(body)
        notes = entity.get("notes", {})

        if event_type == "subscription.charged":
            return WebhookService.handle_razorpay_subscription_charged(db, entity, notes)
        elif event_type == "order.paid":
            return WebhookService.handle_razorpay_order_paid(db, entity, notes)
        elif event_type == "subscription.cancelled":
            return WebhookService.handle_razorpay_subscription_cancelled(db, entity, notes)

        return {"status": "ok"}

    @staticmethod
    def _extract_razorpay_entity(body: dict) -> dict:
        """Extract the entity from a Razorpay webhook payload, checking subscription/order/payment."""
        payload = body.get("payload") or {}
        for key in ("subscription", "order", "payment"):
            entity = payload.get(key, {}).get("entity", {})
            if entity:
                return entity
        return {}
