"""Tests for CreditManager service — the core billing logic."""
from sqlalchemy import select
from tests.conftest import make_user, make_session
from app.services.credit_manager import CreditManager, DeductionResult
from app.models.user import CreditBalance
from app.models.billing import Transaction


class TestCheckBalance:
    def test_sufficient_balance(self, db):
        make_user(db, user_id="cm1")
        mgr = CreditManager(db)
        has_enough, available = mgr.check_balance("cm1", 10.0)
        assert has_enough is True
        assert available == 120.0  # default free minutes

    def test_insufficient_balance(self, db):
        make_user(db, user_id="cm2")
        mgr = CreditManager(db)
        has_enough, available = mgr.check_balance("cm2", 200.0)
        assert has_enough is False
        assert available == 120.0

    def test_exact_balance(self, db):
        make_user(db, user_id="cm3")
        mgr = CreditManager(db)
        has_enough, _ = mgr.check_balance("cm3", 120.0)
        assert has_enough is True


class TestDeductionOrder:
    def test_deduct_paid_first(self, db):
        make_user(db, user_id="do1")
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "do1")
        ).scalar_one_or_none()
        balance.paid_minutes_remaining = 50.0
        balance.paid_minutes_total = 50.0
        db.commit()

        session = make_session(db, "do1")
        mgr = CreditManager(db)
        result = mgr.deduct("do1", 10.0, session.id)

        assert result.success is True
        assert result.paid_used == 10.0
        assert result.payg_used == 0.0
        assert result.free_used == 0.0
        assert result.is_watermarked is False

    def test_deduct_payg_second(self, db):
        make_user(db, user_id="do2")
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "do2")
        ).scalar_one_or_none()
        balance.paid_minutes_remaining = 0.0
        balance.payg_minutes_remaining = 50.0
        balance.free_minutes_remaining = 0.0
        db.commit()

        session = make_session(db, "do2")
        mgr = CreditManager(db)
        result = mgr.deduct("do2", 10.0, session.id)

        assert result.success is True
        assert result.paid_used == 0.0
        assert result.payg_used == 10.0
        assert result.free_used == 0.0
        assert result.is_watermarked is False

    def test_deduct_free_last_with_watermark(self, db):
        make_user(db, user_id="do3")
        session = make_session(db, "do3")
        mgr = CreditManager(db)
        result = mgr.deduct("do3", 10.0, session.id)

        assert result.success is True
        assert result.paid_used == 0.0
        assert result.payg_used == 0.0
        assert result.free_used == 10.0
        assert result.is_watermarked is True

    def test_deduct_mixed_sources(self, db):
        make_user(db, user_id="do4")
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "do4")
        ).scalar_one_or_none()
        balance.paid_minutes_remaining = 5.0
        balance.paid_minutes_total = 5.0
        balance.payg_minutes_remaining = 3.0
        balance.free_minutes_remaining = 120.0
        db.commit()

        session = make_session(db, "do4")
        mgr = CreditManager(db)
        result = mgr.deduct("do4", 10.0, session.id)

        assert result.success is True
        assert result.paid_used == 5.0
        assert result.payg_used == 3.0
        assert result.free_used == 2.0
        assert result.is_watermarked is True  # free minutes used
        assert result.credits_source == "mixed"

    def test_deduct_insufficient_fails(self, db):
        make_user(db, user_id="do5")
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "do5")
        ).scalar_one_or_none()
        balance.free_minutes_remaining = 5.0
        db.commit()

        session = make_session(db, "do5")
        mgr = CreditManager(db)
        result = mgr.deduct("do5", 10.0, session.id)

        assert result.success is False
        assert result.error is not None
        assert "Insufficient" in result.error

    def test_deduct_creates_transaction(self, db):
        make_user(db, user_id="do6")
        session = make_session(db, "do6")
        mgr = CreditManager(db)
        mgr.deduct("do6", 5.0, session.id)

        txn = db.execute(
            select(Transaction).where(
                Transaction.user_id == "do6",
                Transaction.type == "credit_deduction",
            )
        ).scalar_one_or_none()
        assert txn is not None
        assert txn.minutes_amount == 5.0

    def test_deduct_updates_balance(self, db):
        make_user(db, user_id="do7")
        mgr = CreditManager(db)
        session = make_session(db, "do7")
        mgr.deduct("do7", 30.0, session.id)

        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "do7")
        ).scalar_one_or_none()
        assert balance.free_minutes_remaining == 90.0  # 120 - 30


class TestRefund:
    def test_refund_to_correct_buckets(self, db):
        make_user(db, user_id="ref1")
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "ref1")
        ).scalar_one_or_none()
        balance.paid_minutes_remaining = 40.0
        balance.free_minutes_remaining = 100.0
        db.commit()

        session = make_session(db, "ref1")
        mgr = CreditManager(db)
        mgr.refund("ref1", session.id, paid_minutes=10.0, free_minutes=20.0)

        db.refresh(balance)
        assert balance.paid_minutes_remaining == 50.0
        assert balance.free_minutes_remaining == 120.0

    def test_refund_creates_transaction(self, db):
        make_user(db, user_id="ref2")
        session = make_session(db, "ref2")
        mgr = CreditManager(db)
        mgr.refund("ref2", session.id, free_minutes=10.0)

        txn = db.execute(
            select(Transaction).where(
                Transaction.user_id == "ref2",
                Transaction.type == "credit_refund",
            )
        ).scalar_one_or_none()
        assert txn is not None
        assert txn.minutes_amount == 10.0


class TestAddMinutes:
    def test_add_paid_minutes(self, db):
        make_user(db, user_id="am1")
        mgr = CreditManager(db)
        mgr.add_paid_minutes("am1", 100.0, provider="stripe", provider_ref="sub_123")

        balance = mgr.get_balance("am1")
        assert balance.paid_minutes_remaining == 100.0
        assert balance.paid_minutes_total == 100.0

    def test_add_payg_minutes_accumulates(self, db):
        make_user(db, user_id="am2")
        mgr = CreditManager(db)
        mgr.add_payg_minutes("am2", 100.0, amount=200, currency="USD",
                             provider="stripe", provider_ref="cs_1")
        mgr.add_payg_minutes("am2", 100.0, amount=200, currency="USD",
                             provider="stripe", provider_ref="cs_2")

        balance = mgr.get_balance("am2")
        assert balance.payg_minutes_remaining == 200.0

    def test_add_paid_resets_not_accumulates(self, db):
        make_user(db, user_id="am3")
        mgr = CreditManager(db)
        mgr.add_paid_minutes("am3", 100.0, provider="stripe", provider_ref="sub_1")
        mgr.add_paid_minutes("am3", 500.0, provider="stripe", provider_ref="sub_2")

        balance = mgr.get_balance("am3")
        # Paid minutes are RESET (new billing cycle), not accumulated
        assert balance.paid_minutes_remaining == 500.0


class TestDeductionResult:
    def test_credits_source_paid(self):
        r = DeductionResult(success=True, paid_used=10, payg_used=0, free_used=0, is_watermarked=False)
        assert r.credits_source == "paid"

    def test_credits_source_free(self):
        r = DeductionResult(success=True, paid_used=0, payg_used=0, free_used=10, is_watermarked=True)
        assert r.credits_source == "free"

    def test_credits_source_mixed(self):
        r = DeductionResult(success=True, paid_used=5, payg_used=0, free_used=5, is_watermarked=True)
        assert r.credits_source == "mixed"

    def test_total_used(self):
        r = DeductionResult(success=True, paid_used=3, payg_used=2, free_used=1, is_watermarked=True)
        assert r.total_used == 6.0
