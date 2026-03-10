"""Tests for CreditManager.deduct_manual_credits."""

import pytest
from sqlalchemy import select
from app.models.user import CreditBalance
from app.services.credit_manager import CreditManager
from tests.conftest import make_user, TEST_USER_ID


class TestDeductManualCredits:

    def test_pro_no_deduction(self, db):
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")
        cm = CreditManager(db)
        result = cm.deduct_manual_credits(TEST_USER_ID, 5.0, "sess-1", "pro")
        assert result.success is True
        assert result.total_used == 0.0

    def test_pro_max_no_deduction(self, db):
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro_max")
        cm = CreditManager(db)
        result = cm.deduct_manual_credits(TEST_USER_ID, 5.0, "sess-1", "pro_max")
        assert result.success is True

    def test_lite_deducts_from_manual_pool(self, db):
        user = make_user(db, user_id=TEST_USER_ID, plan_tier="lite")
        balance = db.execute(select(CreditBalance).where(CreditBalance.user_id == TEST_USER_ID)).scalar_one()
        balance.manual_clip_minutes_remaining = 100.0
        db.commit()

        cm = CreditManager(db)
        result = cm.deduct_manual_credits(TEST_USER_ID, 5.0, "sess-1", "lite")

        assert result.success is True
        db.refresh(balance)
        assert balance.manual_clip_minutes_remaining == pytest.approx(95.0)

    def test_free_deducts_from_manual_pool(self, db):
        make_user(db, user_id=TEST_USER_ID, plan_tier="free")
        balance = db.execute(select(CreditBalance).where(CreditBalance.user_id == TEST_USER_ID)).scalar_one()
        balance.manual_clip_minutes_remaining = 120.0
        db.commit()

        cm = CreditManager(db)
        result = cm.deduct_manual_credits(TEST_USER_ID, 2.0, "sess-1", "free")

        assert result.success is True
        assert result.is_watermarked is True  # Free tier is watermarked

    def test_falls_through_to_payg(self, db):
        make_user(db, user_id=TEST_USER_ID, plan_tier="lite")
        balance = db.execute(select(CreditBalance).where(CreditBalance.user_id == TEST_USER_ID)).scalar_one()
        balance.manual_clip_minutes_remaining = 2.0
        balance.payg_minutes_remaining = 10.0
        db.commit()

        cm = CreditManager(db)
        result = cm.deduct_manual_credits(TEST_USER_ID, 5.0, "sess-1", "lite")

        assert result.success is True
        db.refresh(balance)
        assert balance.manual_clip_minutes_remaining == pytest.approx(0.0)
        assert balance.payg_minutes_remaining == pytest.approx(7.0)

    def test_insufficient_minutes_rejected(self, db):
        make_user(db, user_id=TEST_USER_ID, plan_tier="lite")
        # No manual minutes, no PAYG

        cm = CreditManager(db)
        result = cm.deduct_manual_credits(TEST_USER_ID, 5.0, "sess-1", "lite")

        assert result.success is False
        assert "Insufficient" in result.error

    def test_does_not_fall_through_to_ai_pool(self, db):
        """Manual deduction should NOT use paid (AI) minutes."""
        make_user(db, user_id=TEST_USER_ID, plan_tier="lite")
        balance = db.execute(select(CreditBalance).where(CreditBalance.user_id == TEST_USER_ID)).scalar_one()
        balance.paid_minutes_remaining = 100.0  # Lots of AI minutes
        balance.manual_clip_minutes_remaining = 0.0
        balance.payg_minutes_remaining = 0.0
        db.commit()

        cm = CreditManager(db)
        result = cm.deduct_manual_credits(TEST_USER_ID, 5.0, "sess-1", "lite")

        assert result.success is False  # Should fail, not use AI pool
