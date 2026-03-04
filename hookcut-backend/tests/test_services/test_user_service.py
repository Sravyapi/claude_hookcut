"""Tests for UserService — user profile, balance, and history business logic."""
import pytest
from sqlalchemy import select

from tests.conftest import make_user, make_session
from app.exceptions import UserNotFoundError, InvalidStateError
from app.models.user import CreditBalance
from app.services.user_service import UserService


class TestGetBalance:
    def test_returns_default_free_balance(self, db):
        make_user(db, user_id="ub1")
        result = UserService.get_balance(db, "ub1")

        assert result.free_minutes_remaining == 120.0
        assert result.free_minutes_total == 120.0
        assert result.paid_minutes_remaining == 0.0
        assert result.paid_minutes_total == 0.0
        assert result.payg_minutes_remaining == 0.0
        assert result.total_available == 120.0

    def test_reflects_modified_balance(self, db):
        make_user(db, user_id="ub2")
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == "ub2")
        ).scalar_one_or_none()
        balance.paid_minutes_remaining = 50.0
        balance.paid_minutes_total = 100.0
        balance.payg_minutes_remaining = 25.0
        balance.free_minutes_remaining = 80.0
        db.commit()

        result = UserService.get_balance(db, "ub2")

        assert result.paid_minutes_remaining == 50.0
        assert result.paid_minutes_total == 100.0
        assert result.payg_minutes_remaining == 25.0
        assert result.free_minutes_remaining == 80.0
        assert result.total_available == 155.0  # 50 + 25 + 80


class TestGetHistory:
    def test_returns_empty_for_no_sessions(self, db):
        make_user(db, user_id="uh1")
        result = UserService.get_history(db, "uh1", page=1, per_page=10)

        assert result["sessions"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["per_page"] == 10

    def test_returns_sessions_for_user(self, db):
        make_user(db, user_id="uh2")
        make_session(db, "uh2", video_id="vid1")
        make_session(db, "uh2", video_id="vid2")

        result = UserService.get_history(db, "uh2", page=1, per_page=10)

        assert result["total"] == 2
        assert len(result["sessions"]) == 2

    def test_session_fields_are_correct(self, db):
        make_user(db, user_id="uh3")
        session = make_session(db, "uh3", video_id="testVid", status="hooks_ready")

        result = UserService.get_history(db, "uh3", page=1, per_page=10)

        s = result["sessions"][0]
        assert s["id"] == session.id
        assert s["video_title"] == "Test Video"
        assert s["video_id"] == "testVid"
        assert s["niche"] == "Generic"
        assert s["language"] == "English"
        assert s["status"] == "hooks_ready"
        assert s["minutes_charged"] == 5.0
        assert "created_at" in s

    def test_pagination_first_page(self, db):
        make_user(db, user_id="uh4")
        for i in range(5):
            make_session(db, "uh4", video_id=f"vid{i}")

        result = UserService.get_history(db, "uh4", page=1, per_page=2)

        assert result["total"] == 5
        assert len(result["sessions"]) == 2
        assert result["page"] == 1
        assert result["per_page"] == 2

    def test_pagination_second_page(self, db):
        make_user(db, user_id="uh5")
        for i in range(5):
            make_session(db, "uh5", video_id=f"vid{i}")

        result = UserService.get_history(db, "uh5", page=2, per_page=2)

        assert result["total"] == 5
        assert len(result["sessions"]) == 2

    def test_pagination_last_page_partial(self, db):
        make_user(db, user_id="uh6")
        for i in range(5):
            make_session(db, "uh6", video_id=f"vid{i}")

        result = UserService.get_history(db, "uh6", page=3, per_page=2)

        assert result["total"] == 5
        assert len(result["sessions"]) == 1  # only 1 remaining

    def test_does_not_return_other_users_sessions(self, db):
        make_user(db, user_id="uh7")
        make_user(db, user_id="uh8")
        make_session(db, "uh7", video_id="vid_u7")
        make_session(db, "uh8", video_id="vid_u8")

        result = UserService.get_history(db, "uh7", page=1, per_page=10)

        assert result["total"] == 1
        assert result["sessions"][0]["video_id"] == "vid_u7"

    def test_page_zero_treated_as_page_one(self, db):
        make_user(db, user_id="uh9")
        make_session(db, "uh9", video_id="vid0")

        result = UserService.get_history(db, "uh9", page=0, per_page=10)

        assert result["total"] == 1
        assert len(result["sessions"]) == 1
        assert result["page"] == 0  # returns raw page value


class TestGetProfile:
    def test_returns_user_profile(self, db):
        make_user(db, user_id="up1", currency="INR", plan_tier="pro")

        result = UserService.get_profile(db, "up1")

        assert result["id"] == "up1"
        assert result["email"] == "up1@test.com"
        assert result["currency"] == "INR"
        assert result["plan_tier"] == "pro"
        assert result["role"] == "user"
        assert "created_at" in result

    def test_raises_for_nonexistent_user(self, db):
        with pytest.raises(UserNotFoundError):
            UserService.get_profile(db, "nonexistent-user")

    def test_returns_admin_role(self, db):
        from app.models.user import User
        user = User(id="up2", email="admin@test.com", role="admin")
        db.add(user)
        db.flush()
        balance = CreditBalance(user_id="up2")
        db.add(balance)
        db.commit()

        result = UserService.get_profile(db, "up2")

        assert result["role"] == "admin"


class TestUpdateCurrency:
    def test_updates_to_inr(self, db):
        make_user(db, user_id="uc1", currency="USD")

        result = UserService.update_currency(db, "uc1", "INR")

        assert result == {"currency": "INR"}
        from app.models.user import User
        user = db.get(User, "uc1")
        assert user.currency == "INR"

    def test_updates_to_usd(self, db):
        make_user(db, user_id="uc2", currency="INR")

        result = UserService.update_currency(db, "uc2", "USD")

        assert result == {"currency": "USD"}

    def test_raises_for_invalid_currency(self, db):
        make_user(db, user_id="uc3")

        with pytest.raises(InvalidStateError) as exc_info:
            UserService.update_currency(db, "uc3", "EUR")
        assert "INR or USD" in exc_info.value.detail

    def test_raises_for_nonexistent_user(self, db):
        with pytest.raises(UserNotFoundError):
            UserService.update_currency(db, "nonexistent", "USD")

    def test_noop_when_same_currency(self, db):
        make_user(db, user_id="uc4", currency="USD")

        result = UserService.update_currency(db, "uc4", "USD")

        assert result == {"currency": "USD"}
