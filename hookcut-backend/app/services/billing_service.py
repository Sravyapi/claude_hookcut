"""
BillingService — owns all billing/checkout business logic.

Routers call these static methods and convert HookCutError to HTTPException.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import UserNotFoundError, InvalidStateError, PaymentProcessingError
from app.models.user import User, CreditBalance
from app.schemas.billing import PlanInfo, PlansResponse
from app.services.analytics import track as track_event, identify as identify_user
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


def _ensure_payments_enabled() -> None:
    """Guard: raise InvalidStateError if V0 mode is active (payments disabled)."""
    if get_settings().FEATURE_V0_MODE:
        raise InvalidStateError(
            "Payment processing not available in V0 mode."
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
        Uses upsert to avoid duplicate user race conditions on concurrent logins.
        Returns dict with user_id, is_new, plan_tier, role.
        """
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        # Check if user already exists (to determine is_new)
        existing = db.get(User, user_id)
        is_new = existing is None

        # Upsert user — idempotent on concurrent logins
        insert_stmt = pg_insert(User).values(
            id=user_id,
            email=email,
            currency="USD",
        )
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={"updated_at": datetime.now(timezone.utc), "email": insert_stmt.excluded.email},
        )
        db.execute(stmt)
        db.flush()

        # Create credit balance only for genuinely new users
        if is_new:
            balance_stmt = pg_insert(CreditBalance).values(
                user_id=user_id,
            ).on_conflict_do_nothing()
            db.execute(balance_stmt)

        db.commit()

        if is_new:
            identify_user(user_id, {"email": email})
            track_event(user_id, "user_signed_up", {"email": email})

        # Refresh to get current DB state (plan_tier, role, etc.)
        user = db.get(User, user_id)
        return {
            "user_id": user_id,
            "is_new": is_new,
            "plan_tier": user.plan_tier if user else "free",
            "role": user.role if user else "user",
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

        if not settings.STRIPE_WEBHOOK_SECRET:
            raise InvalidStateError("Stripe webhook secret is not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            raise InvalidStateError("Invalid webhook signature")

        from app.services.webhook_service import WebhookService

        event_type = event["type"]
        event_id = event["id"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            return WebhookService.handle_stripe_checkout_completed(db, data, event_id)
        elif event_type == "invoice.paid":
            return WebhookService.handle_stripe_invoice_paid(db, data, event_id)
        elif event_type == "customer.subscription.deleted":
            return WebhookService.handle_stripe_subscription_deleted(db, data, event_id)

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

        if not settings.RAZORPAY_WEBHOOK_SECRET:
            raise InvalidStateError("Razorpay webhook secret is not configured")

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
        # Razorpay has no global event id; compose one from event type + entity id.
        razorpay_event_id = f"{event_type}:{entity.get('id', '')}"

        if event_type == "subscription.charged":
            return WebhookService.handle_razorpay_subscription_charged(
                db, entity, notes, razorpay_event_id
            )
        elif event_type == "order.paid":
            return WebhookService.handle_razorpay_order_paid(
                db, entity, notes, razorpay_event_id
            )
        elif event_type == "subscription.cancelled":
            return WebhookService.handle_razorpay_subscription_cancelled(
                db, entity, notes, razorpay_event_id
            )

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
