"""Tests for User, CreditBalance, and Subscription models."""
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from tests.conftest import make_user
from app.models.user import User, CreditBalance, Subscription


class TestUser:
    def test_create_user(self, db):
        user = make_user(db, user_id="u1", email="u1@test.com")
        assert user.id == "u1"
        assert user.email == "u1@test.com"
        assert user.currency == "USD"
        assert user.plan_tier == "free"

    def test_user_defaults(self, db):
        user = make_user(db, user_id="u2")
        assert user.plan_tier == "free"
        assert user.currency == "USD"
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_currency_choices(self, db):
        user_inr = make_user(db, user_id="u3", currency="INR")
        assert user_inr.currency == "INR"

    def test_user_plan_tiers(self, db):
        for tier in ("free", "lite", "pro"):
            user = make_user(db, user_id=f"tier-{tier}", plan_tier=tier)
            assert user.plan_tier == tier

    def test_user_unique_email(self, db):
        make_user(db, user_id="u-dup1", email="dup@test.com")
        import pytest
        with pytest.raises(Exception):
            make_user(db, user_id="u-dup2", email="dup@test.com")
        db.rollback()  # Reset session after IntegrityError


class TestCreditBalance:
    def test_default_balance(self, db):
        user = make_user(db, user_id="cb1")
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "cb1")
        ).scalar_one_or_none()
        assert balance is not None
        assert balance.paid_minutes_remaining == 0.0
        assert balance.free_minutes_remaining == 120.0
        assert balance.payg_minutes_remaining == 0.0

    def test_total_available(self, db):
        user = make_user(db, user_id="cb2")
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "cb2")
        ).scalar_one_or_none()
        balance.paid_minutes_remaining = 50.0
        balance.payg_minutes_remaining = 30.0
        db.commit()
        assert balance.total_available == 200.0  # 50 + 30 + 120

    def test_balance_relationship(self, db):
        user = make_user(db, user_id="cb3")
        db.refresh(user)
        assert user.credit_balance is not None
        assert user.credit_balance.user_id == "cb3"

    def test_update_balance(self, db):
        make_user(db, user_id="cb4")
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "cb4")
        ).scalar_one_or_none()
        balance.paid_minutes_remaining = 100.0
        balance.paid_minutes_total = 100.0
        db.commit()
        db.refresh(balance)
        assert balance.paid_minutes_remaining == 100.0
        assert balance.paid_minutes_total == 100.0


class TestSubscription:
    def test_create_subscription(self, db):
        make_user(db, user_id="sub1")
        now = datetime.now(timezone.utc)
        sub = Subscription(
            user_id="sub1",
            plan_tier="lite",
            currency="USD",
            provider="stripe",
            provider_subscription_id="sub_test123",
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        assert sub.plan_tier == "lite"
        assert sub.status == "active"
        assert sub.provider == "stripe"

    def test_subscription_relationship(self, db):
        user = make_user(db, user_id="sub2")
        now = datetime.now(timezone.utc)
        sub = Subscription(
            user_id="sub2",
            plan_tier="pro",
            currency="INR",
            provider="razorpay",
            provider_subscription_id="rpay_test123",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        db.add(sub)
        db.commit()
        db.refresh(user)
        assert len(user.subscriptions) == 1
        assert user.subscriptions[0].provider == "razorpay"
