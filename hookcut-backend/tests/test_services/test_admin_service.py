"""Tests for AdminService — dashboard, user management, rule CRUD, audit log."""
import pytest

from tests.conftest import make_user, make_session, TEST_USER_ID
from app.exceptions import ResourceNotFoundError
from app.models.admin import AdminAuditLog, PromptRule
from app.services.admin_service import AdminService


def make_admin(db, user_id="admin-svc-1", email="admin@svc.test"):
    """Create an admin user."""
    from app.models.user import User, CreditBalance
    user = User(id=user_id, email=email, role="admin", plan_tier="pro", currency="USD")
    db.add(user)
    db.flush()
    db.add(CreditBalance(user_id=user_id))
    db.commit()
    db.refresh(user)
    return user


# ─── Dashboard Stats ────────────────────────────────────────────────────────

class TestGetDashboardStats:
    def test_returns_required_keys(self, db):
        stats = AdminService.get_dashboard_stats(db)
        for key in ("total_users", "total_sessions", "total_shorts", "active_subscriptions", "recent_sessions"):
            assert key in stats

    def test_counts_users(self, db):
        make_user(db, user_id="ds1")
        make_user(db, user_id="ds2")
        stats = AdminService.get_dashboard_stats(db)
        assert stats["total_users"] >= 2

    def test_recent_sessions_limited_to_10(self, db):
        user = make_user(db, user_id="ds3")
        for i in range(12):
            make_session(db, user_id=user.id, video_id=f"vid{i:03d}")
        stats = AdminService.get_dashboard_stats(db)
        assert len(stats["recent_sessions"]) <= 10

    def test_recent_sessions_include_user_email(self, db):
        user = make_user(db, user_id="ds4", email="stats@test.com")
        make_session(db, user_id=user.id)
        stats = AdminService.get_dashboard_stats(db)
        emails = [s["user_email"] for s in stats["recent_sessions"]]
        assert "stats@test.com" in emails


# ─── List Users ─────────────────────────────────────────────────────────────

class TestListUsers:
    def test_returns_paginated_structure(self, db):
        result = AdminService.list_users(db)
        assert "users" in result
        assert "total" in result
        assert "page" in result
        assert "per_page" in result

    def test_pagination_page_2(self, db):
        for i in range(25):
            make_user(db, user_id=f"pag{i:03d}")
        page1 = AdminService.list_users(db, page=1, per_page=10)
        page2 = AdminService.list_users(db, page=2, per_page=10)
        ids1 = {u["id"] for u in page1["users"]}
        ids2 = {u["id"] for u in page2["users"]}
        assert ids1.isdisjoint(ids2)

    def test_user_has_session_count(self, db):
        user = make_user(db, user_id="sc1")
        make_session(db, user_id=user.id)
        make_session(db, user_id=user.id, video_id="vid2")
        result = AdminService.list_users(db, per_page=50)
        user_row = next(u for u in result["users"] if u["id"] == user.id)
        assert user_row["session_count"] == 2


# ─── Update User Role ────────────────────────────────────────────────────────

class TestUpdateUserRole:
    def test_changes_role(self, db):
        admin = make_admin(db)
        target = make_user(db, user_id="role1")
        AdminService.update_user_role(db, target.id, "admin", admin)
        db.refresh(target)
        assert target.role == "admin"

    def test_creates_audit_log(self, db):
        admin = make_admin(db)
        target = make_user(db, user_id="role2")
        AdminService.update_user_role(db, target.id, "admin", admin)
        log = db.query(AdminAuditLog).filter_by(resource_id=target.id).first()
        assert log is not None
        assert log.action == "role_changed"

    def test_raises_for_missing_user(self, db):
        admin = make_admin(db)
        with pytest.raises(ResourceNotFoundError):
            AdminService.update_user_role(db, "nonexistent-id", "admin", admin)


# ─── Prompt Rule CRUD ────────────────────────────────────────────────────────

class TestCreateRule:
    def test_creates_rule_with_explicit_key(self, db):
        admin = make_admin(db)
        rule = AdminService.create_rule(db, title="Test Rule", content="Do X", rule_key="T1", admin_user=admin)
        assert rule.rule_key == "T1"
        assert rule.title == "Test Rule"
        assert rule.is_active is True
        assert rule.is_base_rule is False

    def test_creates_rule_auto_assigns_key(self, db):
        admin = make_admin(db)
        rule = AdminService.create_rule(db, title="Auto Key", content="Some content", rule_key=None, admin_user=admin)
        assert rule.rule_key is not None
        assert len(rule.rule_key) >= 1

    def test_creates_audit_log(self, db):
        admin = make_admin(db)
        rule = AdminService.create_rule(db, title="Audit Rule", content="...", rule_key="X9", admin_user=admin)
        log = db.query(AdminAuditLog).filter_by(resource_id=rule.id).first()
        assert log is not None
        assert log.action == "prompt_rule_created"


class TestListRules:
    def test_returns_list(self, db):
        rules = AdminService.list_rules(db)
        assert isinstance(rules, list)

    def test_only_active_rules(self, db):
        admin = make_admin(db)
        r = AdminService.create_rule(db, title="Active", content="x", rule_key="AA", admin_user=admin)
        # Deactivate it directly
        r.is_active = False
        db.commit()
        rules = AdminService.list_rules(db)
        ids = [rule.id for rule in rules]
        assert r.id not in ids

    def test_get_active_rules_as_dicts(self, db):
        admin = make_admin(db)
        AdminService.create_rule(db, title="Dict Rule", content="rule content", rule_key="BB", admin_user=admin)
        dicts = AdminService.get_active_rules_as_dicts(db)
        assert all("rule_key" in d and "content" in d for d in dicts)


# ─── Audit Log ───────────────────────────────────────────────────────────────

class TestCreateAuditLog:
    def test_creates_and_flushes(self, db):
        admin = make_admin(db)
        log = AdminService.create_audit_log(
            db,
            admin_user=admin,
            action="test_action",
            resource_type="user",
            resource_id="some-id",
            before_state={"x": 1},
            after_state={"x": 2},
            description="Test audit entry",
        )
        db.commit()
        assert log.id is not None
        assert log.action == "test_action"
        assert log.before_state == {"x": 1}
        assert log.after_state == {"x": 2}


class TestListAuditLogs:
    def test_returns_paginated_structure(self, db):
        result = AdminService.list_audit_logs(db)
        assert "logs" in result
        assert "total" in result

    def test_action_filter(self, db):
        admin = make_admin(db)
        AdminService.create_audit_log(
            db, admin, "specific_action", "user", "u1", None, None, "desc"
        )
        db.commit()
        result = AdminService.list_audit_logs(db, action="specific_action")
        assert result["total"] >= 1
        assert all(log["action"] == "specific_action" for log in result["logs"])
