import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, Subscription
from app.models.billing import Transaction
from app.services.credit_manager import CreditManager
from app.services.payment_service import PLAN_MINUTES

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def activate_subscription(
        self,
        user_id: str,
        plan_tier: str,
        provider: str,
        subscription_id: str,
        currency: str,
    ) -> None:
        """Activate or update a subscription and provision credits."""
        user = self.db.get(User, user_id)
        if not user:
            return

        user.plan_tier = plan_tier

        # Create or update subscription record
        sub = self.db.execute(
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
            self.db.add(sub)

        # Provision paid minutes
        minutes = PLAN_MINUTES.get(plan_tier, 0)
        if minutes > 0:
            credit_mgr = CreditManager(self.db)
            credit_mgr.add_paid_minutes(
                user_id, minutes,
                provider=provider, provider_ref=subscription_id,
            )

        # Log transaction
        txn = Transaction(
            user_id=user_id,
            type="subscription_payment",
            money_amount=0,
            currency=currency,
            provider=provider,
            provider_ref=subscription_id,
            description=f"Subscription: {plan_tier} via {provider}",
        )
        self.db.add(txn)
        self.db.commit()
