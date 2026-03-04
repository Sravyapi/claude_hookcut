"""
WebhookService — handles payment provider webhook event processing.
Delegates from billing router after signature verification.
"""
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User, Subscription
from app.services.credit_manager import CreditManager
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PLAN_MINUTES

logger = logging.getLogger(__name__)


class WebhookService:
    @staticmethod
    def handle_stripe_checkout_completed(db: Session, data: dict) -> dict:
        """Handle Stripe checkout.session.completed event."""
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")
        if not user_id:
            logger.warning("Stripe checkout missing user_id in metadata")
            return {"status": "ignored"}

        if metadata.get("purchase_type") == "payg":
            minutes = int(metadata.get("minutes", 100))
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

    @staticmethod
    def handle_stripe_invoice_paid(db: Session, data: dict) -> dict:
        """Handle Stripe invoice.paid event (subscription renewal)."""
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

    @staticmethod
    def handle_stripe_subscription_deleted(db: Session, data: dict) -> dict:
        """Handle Stripe customer.subscription.deleted event."""
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
            db.commit()
            logger.info(f"Subscription cancelled for {sub.user_id}")
        return {"status": "ok"}

    @staticmethod
    def handle_razorpay_subscription_charged(db: Session, entity: dict, notes: dict) -> dict:
        """Handle Razorpay subscription.charged event."""
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

    @staticmethod
    def handle_razorpay_order_paid(db: Session, entity: dict, notes: dict) -> dict:
        """Handle Razorpay order.paid event."""
        user_id = notes.get("user_id")
        if not user_id:
            return {"status": "ignored"}
        if notes.get("purchase_type") == "payg":
            minutes = int(notes.get("minutes", 100))
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

    @staticmethod
    def handle_razorpay_subscription_cancelled(db: Session, entity: dict, notes: dict) -> dict:
        """Handle Razorpay subscription.cancelled event."""
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
            db.commit()
            logger.info(f"Razorpay subscription cancelled for {user_id}")
        return {"status": "ok"}
