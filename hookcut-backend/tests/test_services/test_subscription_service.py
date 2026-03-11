"""Tests for SubscriptionService — subscription activation and credit provisioning."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import select

from tests.conftest import make_user, TEST_USER_ID
from app.models.user import User, Subscription, CreditBalance
from app.models.billing import Transaction
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PLAN_MINUTES


# ─── Helpers ────────────────────────────────────────────────────────────────

def _get_active_sub(db, user_id: str, provider: str = "stripe") -> Subscription | None:
    return db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.provider == provider,
            Subscription.status == "active",
        )
    ).scalar_one_or_none()


def _get_balance(db, user_id: str) -> CreditBalance | None:
    return db.execute(
        select(CreditBalance).where(CreditBalance.user_id == user_id)
    ).scalar_one_or_none()


# ─── activate_subscription ───────────────────────────────────────────────────

class TestActivateSubscription:
    def test_happy_path_creates_subscription_record(self, db):
        make_user(db, user_id="ss1")

        SubscriptionService.activate_subscription(
            db, "ss1", "pro", "stripe", "sub_abc123", "USD"
        )

        sub = _get_active_sub(db, "ss1", provider="stripe")
        assert sub is not None
        assert sub.plan_tier == "pro"
        assert sub.provider_subscription_id == "sub_abc123"
        assert sub.currency == "USD"
        assert sub.status == "active"

    def test_happy_path_updates_user_plan_tier(self, db):
        make_user(db, user_id="ss2", plan_tier="free")

        SubscriptionService.activate_subscription(
            db, "ss2", "pro", "stripe", "sub_bbb", "USD"
        )

        db.expire_all()
        user = db.get(User, "ss2")
        assert user.plan_tier == "pro"

    def test_happy_path_provisions_paid_minutes(self, db):
        make_user(db, user_id="ss3")

        SubscriptionService.activate_subscription(
            db, "ss3", "pro", "stripe", "sub_ccc", "USD"
        )

        balance = _get_balance(db, "ss3")
        assert balance is not None
        assert balance.paid_minutes_remaining == PLAN_MINUTES["pro"]
        assert balance.paid_minutes_total == PLAN_MINUTES["pro"]

    def test_happy_path_creates_transaction_record(self, db):
        make_user(db, user_id="ss4")

        SubscriptionService.activate_subscription(
            db, "ss4", "pro", "stripe", "sub_ddd", "INR"
        )

        txn = db.execute(
            select(Transaction).where(
                Transaction.user_id == "ss4",
                Transaction.type == "subscription_payment",
            )
        ).scalar_one_or_none()
        assert txn is not None
        assert txn.minutes_amount == PLAN_MINUTES["pro"]

    def test_lite_plan_provisions_lite_minutes(self, db):
        make_user(db, user_id="ss5")

        SubscriptionService.activate_subscription(
            db, "ss5", "lite", "stripe", "sub_eee", "USD"
        )

        balance = _get_balance(db, "ss5")
        assert balance.paid_minutes_remaining == PLAN_MINUTES["lite"]

    def test_period_dates_set_correctly(self, db):
        make_user(db, user_id="ss6")
        before = datetime.now(timezone.utc)

        SubscriptionService.activate_subscription(
            db, "ss6", "pro", "stripe", "sub_fff", "USD"
        )

        after = datetime.now(timezone.utc)
        sub = _get_active_sub(db, "ss6", provider="stripe")
        # period start must be within test window
        start = sub.current_period_start
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        end = sub.current_period_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        assert before <= start <= after
        # period end should be ~30 days later
        assert abs((end - start).days - 30) <= 1

    def test_unknown_user_is_noop(self, db):
        """activate_subscription returns silently when user does not exist."""
        # Should not raise
        SubscriptionService.activate_subscription(
            db, "nonexistent-user", "pro", "stripe", "sub_zzz", "USD"
        )

        # No subscription or transaction should have been created
        sub = _get_active_sub(db, "nonexistent-user", provider="stripe")
        assert sub is None

        txn = db.execute(
            select(Transaction).where(Transaction.user_id == "nonexistent-user")
        ).scalar_one_or_none()
        assert txn is None

    def test_invalid_plan_tier_provisions_zero_minutes(self, db):
        """An unrecognised plan_tier results in no paid minutes being added (PLAN_MINUTES returns 0)."""
        make_user(db, user_id="ss7")

        SubscriptionService.activate_subscription(
            db, "ss7", "ultra_max_pro", "stripe", "sub_unk", "USD"
        )

        # User plan_tier is still updated (the service sets it unconditionally)
        db.expire_all()
        user = db.get(User, "ss7")
        assert user.plan_tier == "ultra_max_pro"

        # But no paid-minutes transaction was created (0 minutes means no credit call)
        txn = db.execute(
            select(Transaction).where(
                Transaction.user_id == "ss7",
                Transaction.type == "subscription_payment",
            )
        ).scalar_one_or_none()
        assert txn is None

    def test_already_active_subscription_is_updated_not_duplicated(self, db):
        """Calling activate_subscription again for an already-active provider updates the existing row."""
        make_user(db, user_id="ss8")

        # Activate once
        SubscriptionService.activate_subscription(
            db, "ss8", "lite", "stripe", "sub_first", "USD"
        )

        # Activate again (renewal / upgrade) with same provider
        SubscriptionService.activate_subscription(
            db, "ss8", "pro", "stripe", "sub_second", "USD"
        )

        # Only ONE active subscription row for this provider
        subs = db.execute(
            select(Subscription).where(
                Subscription.user_id == "ss8",
                Subscription.provider == "stripe",
                Subscription.status == "active",
            )
        ).scalars().all()
        assert len(subs) == 1

        sub = subs[0]
        assert sub.plan_tier == "pro"
        assert sub.provider_subscription_id == "sub_second"

    def test_different_providers_create_separate_records(self, db):
        """Activating with different providers (stripe vs razorpay) creates separate rows."""
        make_user(db, user_id="ss9")

        SubscriptionService.activate_subscription(
            db, "ss9", "pro", "stripe", "sub_stripe_1", "USD"
        )
        SubscriptionService.activate_subscription(
            db, "ss9", "pro", "razorpay", "sub_rzp_1", "INR"
        )

        stripe_sub = _get_active_sub(db, "ss9", provider="stripe")
        rzp_sub = _get_active_sub(db, "ss9", provider="razorpay")

        assert stripe_sub is not None
        assert rzp_sub is not None
        assert stripe_sub.id != rzp_sub.id

    def test_razorpay_provider_works(self, db):
        make_user(db, user_id="ss10", currency="INR")

        SubscriptionService.activate_subscription(
            db, "ss10", "pro", "razorpay", "rzp_sub_abc", "INR"
        )

        sub = _get_active_sub(db, "ss10", provider="razorpay")
        assert sub is not None
        assert sub.currency == "INR"
        assert sub.provider == "razorpay"

    def test_paid_minutes_reset_on_renewal(self, db):
        """Renewing resets paid_minutes to the new plan allocation (not cumulative)."""
        make_user(db, user_id="ss11")

        SubscriptionService.activate_subscription(
            db, "ss11", "lite", "stripe", "sub_lite_1", "USD"
        )

        # Simulate user spending some minutes
        balance = _get_balance(db, "ss11")
        balance.paid_minutes_remaining = 10.0  # spent most of lite allocation
        db.commit()

        # Renewal / upgrade to pro
        SubscriptionService.activate_subscription(
            db, "ss11", "pro", "stripe", "sub_pro_1", "USD"
        )

        db.expire_all()
        balance = _get_balance(db, "ss11")
        assert balance.paid_minutes_remaining == PLAN_MINUTES["pro"]

    def test_free_minutes_are_not_affected(self, db):
        """Activating a subscription should not touch free_minutes_remaining."""
        make_user(db, user_id="ss12")
        balance = _get_balance(db, "ss12")
        free_before = balance.free_minutes_remaining  # 120.0

        SubscriptionService.activate_subscription(
            db, "ss12", "pro", "stripe", "sub_ggg", "USD"
        )

        db.expire_all()
        balance = _get_balance(db, "ss12")
        assert balance.free_minutes_remaining == free_before
