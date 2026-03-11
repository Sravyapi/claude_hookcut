"""Tests for CreditManager service — the core billing logic."""
import pytest
from contextlib import contextmanager
from unittest.mock import patch, MagicMock, call
from sqlalchemy import select
from tests.conftest import make_user, make_session
from app.services.credit_manager import CreditManager, DeductionResult
from app.models.user import CreditBalance
from app.models.billing import Transaction
from app.exceptions import InsufficientCreditsError


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
        assert result.credits_source == "paid"  # Returns highest-priority source used

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

    def test_credits_source_primary(self):
        r = DeductionResult(success=True, paid_used=5, payg_used=0, free_used=5, is_watermarked=True)
        assert r.credits_source == "paid"  # Returns highest-priority source

    def test_total_used(self):
        r = DeductionResult(success=True, paid_used=3, payg_used=2, free_used=1, is_watermarked=True)
        assert r.total_used == 6.0


class TestConcurrentDeductionSafety:
    """Tests for savepoint/rollback behavior in deduct() and related methods.

    We do NOT spawn real threads — instead we verify rollback semantics by
    mocking db.begin_nested() to track whether rollback() was called, and by
    inspecting DB state after injected failures.
    """

    def _make_tracking_savepoint(self):
        """Return a (context-manager factory, tracker-dict) pair.

        The context manager mimics the interface of a SQLAlchemy nested
        transaction: __enter__ returns itself, __exit__ re-raises exceptions
        (i.e. rolls back) and records that fact in tracker['rolled_back'].
        """
        tracker = {"entered": False, "rolled_back": False, "committed": False}

        @contextmanager
        def _savepoint_cm():
            tracker["entered"] = True
            try:
                yield tracker
                tracker["committed"] = True
            except Exception:
                tracker["rolled_back"] = True
                raise

        return _savepoint_cm, tracker

    # ------------------------------------------------------------------
    # Savepoint mock tests
    # ------------------------------------------------------------------

    def test_savepoint_entered_on_deduct(self, db):
        """deduct() must open a savepoint via db.begin_nested()."""
        make_user(db, user_id="concur0")
        session = make_session(db, "concur0")

        _cm, tracker = self._make_tracking_savepoint()

        mgr = CreditManager(db)
        original_begin_nested = db.begin_nested
        db.begin_nested = _cm

        try:
            mgr.deduct("concur0", 10.0, session.id)
        finally:
            db.begin_nested = original_begin_nested

        assert tracker["entered"] is True

    def test_savepoint_rollback_called_on_mid_transaction_error(self, db):
        """If Transaction insert raises inside the savepoint, rollback is triggered."""
        make_user(db, user_id="concur1")
        session = make_session(db, "concur1")

        balance_before = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "concur1")
        ).scalar_one()
        free_before = balance_before.free_minutes_remaining  # 120.0

        rollback_called = [False]

        # Build a savepoint that delegates to the REAL nested transaction but
        # patches db.add so the Transaction insert raises before the savepoint
        # can commit — causing the context manager's except branch to fire.
        original_begin_nested = db.begin_nested
        original_add = db.add

        @contextmanager
        def _faulting_savepoint():
            # Monkey-patch db.add inside the savepoint so Transaction insert fails
            def _patched_add(obj):
                if isinstance(obj, Transaction):
                    raise RuntimeError("Simulated constraint violation")
                return original_add(obj)

            db.add = _patched_add
            sp = original_begin_nested()  # real savepoint
            try:
                yield sp
            except Exception:
                rollback_called[0] = True
                sp.rollback()
                raise
            finally:
                db.add = original_add

        mgr = CreditManager(db)
        db.begin_nested = _faulting_savepoint

        try:
            mgr.deduct("concur1", 10.0, session.id)
        except Exception:
            pass  # exception propagation is acceptable
        finally:
            db.begin_nested = original_begin_nested

        assert rollback_called[0] is True

        # Balance must be unchanged after rollback
        db.expire_all()
        balance_after = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "concur1")
        ).scalar_one()
        assert balance_after.free_minutes_remaining == free_before

    def test_savepoint_rollback_called_on_refund_error(self, db):
        """If Transaction insert raises inside the refund() savepoint, rollback fires."""
        make_user(db, user_id="concur1r")
        session = make_session(db, "concur1r")

        rollback_called = [False]
        original_begin_nested = db.begin_nested
        original_add = db.add

        @contextmanager
        def _faulting_savepoint():
            def _patched_add(obj):
                if isinstance(obj, Transaction):
                    raise RuntimeError("Simulated constraint violation")
                return original_add(obj)

            db.add = _patched_add
            sp = original_begin_nested()
            try:
                yield sp
            except Exception:
                rollback_called[0] = True
                sp.rollback()
                raise
            finally:
                db.add = original_add

        mgr = CreditManager(db)
        db.begin_nested = _faulting_savepoint

        try:
            mgr.refund("concur1r", session.id, free_minutes=5.0)
        except Exception:
            pass
        finally:
            db.begin_nested = original_begin_nested

        assert rollback_called[0] is True

    def test_savepoint_not_rolled_back_on_success(self, db):
        """On a successful deduction the savepoint is NOT rolled back."""
        make_user(db, user_id="concur_ok")
        session = make_session(db, "concur_ok")

        rollback_called = [False]
        original_begin_nested = db.begin_nested

        @contextmanager
        def _tracking_savepoint():
            sp = original_begin_nested()
            try:
                yield sp
            except Exception:
                rollback_called[0] = True
                sp.rollback()
                raise

        mgr = CreditManager(db)
        db.begin_nested = _tracking_savepoint

        try:
            result = mgr.deduct("concur_ok", 10.0, session.id)
        finally:
            db.begin_nested = original_begin_nested

        assert result.success is True
        assert rollback_called[0] is False

    # ------------------------------------------------------------------
    # DB-state / correctness tests (preserved from original suite)
    # ------------------------------------------------------------------

    def test_insufficient_credits_raises_not_deducts(self, db):
        """When credits are insufficient, no balance change occurs and no Transaction is created."""
        make_user(db, user_id="concur2")

        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "concur2")
        ).scalar_one()
        balance.free_minutes_remaining = 3.0
        balance.paid_minutes_remaining = 0.0
        balance.payg_minutes_remaining = 0.0
        db.commit()

        session = make_session(db, "concur2")
        mgr = CreditManager(db)

        result = mgr.deduct("concur2", 10.0, session.id)

        assert result.success is False
        assert "Insufficient" in result.error

        db.expire_all()
        balance_after = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "concur2")
        ).scalar_one()
        assert balance_after.free_minutes_remaining == 3.0
        assert balance_after.paid_minutes_remaining == 0.0
        assert balance_after.payg_minutes_remaining == 0.0

        txn = db.execute(
            select(Transaction).where(
                Transaction.user_id == "concur2",
                Transaction.type == "credit_deduction",
            )
        ).scalar_one_or_none()
        assert txn is None

    def test_deduction_is_atomic(self, db):
        """A successful deduction spanning multiple buckets commits all changes together."""
        make_user(db, user_id="concur3")

        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "concur3")
        ).scalar_one()
        balance.paid_minutes_remaining = 5.0
        balance.paid_minutes_total = 5.0
        balance.payg_minutes_remaining = 3.0
        balance.free_minutes_remaining = 120.0
        db.commit()

        session = make_session(db, "concur3")
        mgr = CreditManager(db)
        result = mgr.deduct("concur3", 8.0, session.id)

        assert result.success is True
        assert result.paid_used == 5.0
        assert result.payg_used == 3.0
        assert result.free_used == 0.0
        assert result.is_watermarked is False

        db.expire_all()
        balance_after = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "concur3")
        ).scalar_one()

        assert balance_after.paid_minutes_remaining == 0.0
        assert balance_after.payg_minutes_remaining == 0.0
        assert balance_after.free_minutes_remaining == 120.0  # untouched

        txns = db.execute(
            select(Transaction).where(
                Transaction.user_id == "concur3",
                Transaction.type == "credit_deduction",
            )
        ).scalars().all()
        assert len(txns) == 1
        assert txns[0].minutes_amount == 8.0


# ─── claim_free_topup ────────────────────────────────────────────────────────

class TestClaimFreeTopup:
    def test_adds_120_free_minutes(self, db):
        make_user(db, user_id="ft1")

        mgr = CreditManager(db)
        balance = mgr.claim_free_topup("ft1")

        # Started with 120, added 120 → 240
        assert balance.free_minutes_remaining == 240.0
        assert balance.free_minutes_total == 240.0

    def test_decrements_topups_remaining(self, db):
        make_user(db, user_id="ft2")

        mgr = CreditManager(db)
        mgr.claim_free_topup("ft2")

        balance = mgr.get_balance("ft2")
        assert balance.free_topups_remaining == 2  # started at 3

    def test_creates_free_topup_transaction(self, db):
        make_user(db, user_id="ft3")

        mgr = CreditManager(db)
        mgr.claim_free_topup("ft3")

        txn = db.execute(
            select(Transaction).where(
                Transaction.user_id == "ft3",
                Transaction.type == "free_topup",
            )
        ).scalar_one_or_none()
        assert txn is not None
        assert txn.minutes_amount == 120.0

    def test_multiple_topups_accumulate(self, db):
        make_user(db, user_id="ft4")

        mgr = CreditManager(db)
        mgr.claim_free_topup("ft4")
        mgr.claim_free_topup("ft4")

        balance = mgr.get_balance("ft4")
        assert balance.free_minutes_remaining == 360.0  # 120 + 120 + 120
        assert balance.free_topups_remaining == 1

    def test_exhausted_topups_raises(self, db):
        make_user(db, user_id="ft5")

        # Exhaust all 3 free top-ups
        mgr = CreditManager(db)
        mgr.claim_free_topup("ft5")
        mgr.claim_free_topup("ft5")
        mgr.claim_free_topup("ft5")

        # 4th attempt should raise InsufficientCreditsError
        with pytest.raises(InsufficientCreditsError) as exc_info:
            mgr.claim_free_topup("ft5")
        assert "No free top-ups remaining" in str(exc_info.value)

    def test_topup_savepoint_entered(self, db):
        """claim_free_topup() must use a savepoint (begin_nested)."""
        make_user(db, user_id="ft6")

        entered = [False]
        original_begin_nested = db.begin_nested

        @contextmanager
        def _tracking():
            entered[0] = True
            sp = original_begin_nested()
            try:
                yield sp
            except Exception:
                sp.rollback()
                raise

        mgr = CreditManager(db)
        db.begin_nested = _tracking

        try:
            mgr.claim_free_topup("ft6")
        finally:
            db.begin_nested = original_begin_nested

        assert entered[0] is True

    def test_topup_rollback_on_error(self, db):
        """If an error occurs inside the topup savepoint, balance is not changed."""
        make_user(db, user_id="ft7")

        rollback_called = [False]
        original_begin_nested = db.begin_nested
        original_add = db.add

        @contextmanager
        def _faulting_savepoint():
            def _patched_add(obj):
                if isinstance(obj, Transaction):
                    raise RuntimeError("Simulated DB error")
                return original_add(obj)

            db.add = _patched_add
            sp = original_begin_nested()
            try:
                yield sp
            except Exception:
                rollback_called[0] = True
                sp.rollback()
                raise
            finally:
                db.add = original_add

        mgr = CreditManager(db)
        db.begin_nested = _faulting_savepoint
        balance_before = mgr.get_balance("ft7")
        free_before = balance_before.free_minutes_remaining

        try:
            mgr.claim_free_topup("ft7")
        except Exception:
            pass
        finally:
            db.begin_nested = original_begin_nested

        assert rollback_called[0] is True

        db.expire_all()
        balance_after = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "ft7")
        ).scalar_one()
        assert balance_after.free_minutes_remaining == free_before
