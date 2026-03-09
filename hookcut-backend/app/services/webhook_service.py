"""
WebhookService — handles payment provider webhook event processing.
Delegates from billing router after signature verification.
"""
import logging
from typing import Callable
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User, Subscription
from app.models.billing import ProcessedWebhook
from app.services.credit_manager import CreditManager
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PLAN_MINUTES

logger = logging.getLogger(__name__)

# Maximum minutes that can be granted in a single PAYG purchase.
# Guards against metadata tampering (e.g., minutes=999999 injected via Stripe metadata).
MAX_MINUTES_PER_PURCHASE = 10_000


class WebhookService:

    @staticmethod
    def _is_duplicate(db: Session, provider: str, event_id: str) -> bool:
        """Return True if this (provider, event_id) was already processed."""
        row = db.get(ProcessedWebhook, {"provider": provider, "event_id": event_id})
        return row is not None

    @staticmethod
    def _mark_processed(db: Session, provider: str, event_id: str) -> None:
        """Insert an idempotency record. Must be called inside an open transaction."""
        db.add(ProcessedWebhook(provider=provider, event_id=event_id))

    @staticmethod
    def _with_idempotency(
        db: Session, provider: str, event_id: str,
        handler_fn: Callable[[Session], dict],
    ) -> dict:
        """Wrap a handler with duplicate check, mark-processed, and commit.

        If the event was already processed, returns {"status": "duplicate"}.
        Otherwise calls handler_fn(db). If handler_fn returns a result with
        status != "ok" (e.g. "ignored"), skips marking as processed and
        does not commit. Otherwise marks processed and commits.
        """
        if WebhookService._is_duplicate(db, provider, event_id):
            logger.info(f"Duplicate {provider} event ignored: {event_id}")
            return {"status": "duplicate"}

        result = handler_fn(db)

        # If the handler chose to ignore, don't mark processed or commit
        if result.get("status") == "ignored":
            return result

        WebhookService._mark_processed(db, provider, event_id)
        db.commit()
        return {"status": "ok"}

    @staticmethod
    def handle_stripe_checkout_completed(
        db: Session, data: dict, event_id: str
    ) -> dict:
        """Handle Stripe checkout.session.completed event."""
        def _handle(db: Session) -> dict:
            metadata = data.get("metadata", {})
            user_id = metadata.get("user_id")
            if not user_id:
                logger.warning("Stripe checkout missing user_id in metadata")
                return {"status": "ignored"}

            if metadata.get("purchase_type") == "payg":
                minutes = min(int(metadata.get("minutes", 100)), MAX_MINUTES_PER_PURCHASE)
                credit_mgr = CreditManager(db)
                credit_mgr.add_payg_minutes(
                    user_id, minutes,
                    amount=data.get("amount_total", 0),
                    currency=(data.get("currency", "usd")).upper(),
                    provider="stripe",
                    provider_ref=data.get("id", ""),
                )
                logger.info(f"PAYG: {minutes} minutes provisioned for {user_id}")
            else:
                plan_tier = metadata.get("plan_tier", "lite")
                SubscriptionService(db).activate_subscription(
                    user_id=user_id,
                    plan_tier=plan_tier,
                    provider="stripe",
                    subscription_id=data.get("subscription", data.get("id", "")),
                    currency=(data.get("currency", "usd")).upper(),
                )
                logger.info(f"Subscription: {plan_tier} activated for {user_id}")

            return {"status": "ok"}

        return WebhookService._with_idempotency(db, "stripe", event_id, _handle)

    @staticmethod
    def handle_stripe_invoice_paid(db: Session, data: dict, event_id: str) -> dict:
        """Handle Stripe invoice.paid event (subscription renewal)."""
        def _handle(db: Session) -> dict:
            sub_id = data.get("subscription")
            if sub_id:
                sub = db.execute(
                    select(Subscription).where(
                        Subscription.provider_subscription_id == sub_id,
                        Subscription.provider == "stripe",
                    )
                ).scalar_one_or_none()
                if sub:
                    minutes = PLAN_MINUTES.get(sub.plan_tier, 0)
                    credit_mgr = CreditManager(db)
                    credit_mgr.add_paid_minutes(
                        sub.user_id, minutes,
                        provider="stripe", provider_ref=data.get("id", ""),
                    )
                    logger.info(f"Renewal: {minutes} minutes for {sub.user_id}")

            return {"status": "ok"}

        return WebhookService._with_idempotency(db, "stripe", event_id, _handle)

    @staticmethod
    def handle_stripe_subscription_deleted(
        db: Session, data: dict, event_id: str
    ) -> dict:
        """Handle Stripe customer.subscription.deleted event."""
        def _handle(db: Session) -> dict:
            sub_id = data.get("id")
            sub = db.execute(
                select(Subscription).where(
                    Subscription.provider_subscription_id == sub_id,
                    Subscription.provider == "stripe",
                )
            ).scalar_one_or_none()
            if sub:
                sub.status = "cancelled"
                user = db.get(User, sub.user_id)
                if user:
                    user.plan_tier = "free"
                logger.info(f"Subscription cancelled for {sub.user_id}")

            return {"status": "ok"}

        return WebhookService._with_idempotency(db, "stripe", event_id, _handle)

    @staticmethod
    def handle_razorpay_subscription_charged(
        db: Session, entity: dict, notes: dict, event_id: str
    ) -> dict:
        """Handle Razorpay subscription.charged event."""
        def _handle(db: Session) -> dict:
            user_id = notes.get("user_id")
            if not user_id:
                return {"status": "ignored"}
            plan_tier = notes.get("plan_tier", "lite")
            SubscriptionService(db).activate_subscription(
                user_id=user_id,
                plan_tier=plan_tier,
                provider="razorpay",
                subscription_id=entity.get("id", ""),
                currency="INR",
            )
            logger.info(f"Razorpay subscription charged: {plan_tier} for {user_id}")

            return {"status": "ok"}

        return WebhookService._with_idempotency(db, "razorpay", event_id, _handle)

    @staticmethod
    def handle_razorpay_order_paid(
        db: Session, entity: dict, notes: dict, event_id: str
    ) -> dict:
        """Handle Razorpay order.paid event."""
        def _handle(db: Session) -> dict:
            user_id = notes.get("user_id")
            if not user_id:
                return {"status": "ignored"}
            if notes.get("purchase_type") == "payg":
                minutes = min(int(notes.get("minutes", 100)), MAX_MINUTES_PER_PURCHASE)
                credit_mgr = CreditManager(db)
                credit_mgr.add_payg_minutes(
                    user_id, minutes,
                    amount=entity.get("amount", 0),
                    currency="INR",
                    provider="razorpay",
                    provider_ref=entity.get("id", ""),
                )
                logger.info(f"Razorpay PAYG: {minutes} minutes for {user_id}")

            return {"status": "ok"}

        return WebhookService._with_idempotency(db, "razorpay", event_id, _handle)

    @staticmethod
    def handle_razorpay_subscription_cancelled(
        db: Session, entity: dict, notes: dict, event_id: str
    ) -> dict:
        """Handle Razorpay subscription.cancelled event."""
        def _handle(db: Session) -> dict:
            user_id = notes.get("user_id")
            if not user_id:
                return {"status": "ignored"}
            sub = db.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.provider == "razorpay",
                    Subscription.status == "active",
                )
            ).scalar_one_or_none()
            if sub:
                sub.status = "cancelled"
                user = db.get(User, sub.user_id)
                if user:
                    user.plan_tier = "free"
                logger.info(f"Razorpay subscription cancelled for {user_id}")

            return {"status": "ok"}

        return WebhookService._with_idempotency(db, "razorpay", event_id, _handle)
