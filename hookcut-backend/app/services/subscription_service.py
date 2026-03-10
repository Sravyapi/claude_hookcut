import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, Subscription
from app.services.credit_manager import CreditManager
from app.services.payment_service import PLAN_MINUTES

logger = logging.getLogger(__name__)


class SubscriptionService:
    @staticmethod
    def activate_subscription(
        db: Session,
        user_id: str,
        plan_tier: str,
        provider: str,
        subscription_id: str,
        currency: str,
    ) -> None:
        """Activate or update a subscription and provision credits."""
        user = db.get(User, user_id)
        if not user:
            return

        user.plan_tier = plan_tier

        # Create or update subscription record
        sub = db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.provider == provider,
                Subscription.status == "active",
            )
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if sub:
            sub.plan_tier = plan_tier
            sub.provider_subscription_id = subscription_id
            sub.current_period_start = now
            sub.current_period_end = now + timedelta(days=30)
        else:
            sub = Subscription(
                user_id=user_id,
                plan_tier=plan_tier,
                currency=currency,
                provider=provider,
                provider_subscription_id=subscription_id,
                status="active",
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
            )
            db.add(sub)

        # Provision paid minutes
        minutes = PLAN_MINUTES.get(plan_tier, 0)
        if minutes > 0:
            credit_mgr = CreditManager(db)
            credit_mgr.add_paid_minutes(
                user_id, minutes,
                provider=provider, provider_ref=subscription_id,
            )

        # Transaction already created by add_paid_minutes() above
        db.commit()
