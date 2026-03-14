"""Tests for Transaction and LearningLog models."""
from sqlalchemy import select
from tests.conftest import make_user, make_session
from app.models.billing import Transaction
from app.models.learning import LearningLog


class TestTransaction:
    def test_create_deduction_transaction(self, db):
        make_user(db, user_id="t1")
        session = make_session(db, "t1")
        txn = Transaction(
            user_id="t1",
            type="credit_deduction",
            session_id=session.id,
            minutes_amount=5.0,
            description="Deducted 5.0 min",
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)
        assert txn.type == "credit_deduction"
        assert txn.minutes_amount == 5.0
        assert txn.session_id == session.id

    def test_create_payment_transaction(self, db):
        make_user(db, user_id="t2")
        txn = Transaction(
            user_id="t2",
            type="subscription_payment",
            minutes_amount=100.0,
            money_amount=700,
            currency="USD",
            provider="stripe",
            provider_ref="sub_abc123",
            description="Subscription: 100 min provisioned",
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)
        assert txn.money_amount == 700
        assert txn.provider == "stripe"



class TestLearningLog:
    def test_create_learning_log(self, db):
        make_user(db, user_id="l1")
        session = make_session(db, "l1")
        log = LearningLog(
            session_id=session.id,
            event_type="hook_selected",
            hook_id="hook-123",
            video_id="dQw4w9WgXcQ",
            niche="Generic",
            language="English",
            event_metadata={"selection_order": 1},
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        assert log.event_type == "hook_selected"
        assert log.event_metadata["selection_order"] == 1

