"""Tests for AdminProviderService — provider listing, updates, primary switching, API keys."""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import select

from tests.conftest import make_user
from app.models.admin import ProviderConfig, AdminAuditLog
from app.models.user import User, CreditBalance
from app.services.admin_provider_service import AdminProviderService
from app.exceptions import ResourceNotFoundError, InvalidStateError


# ─── Fixtures / helpers ───────────────────────────────────────────────────────


def make_admin(db, user_id="adm-prov-1", email="admin@provider.test"):
    """Create an admin user."""
    user = User(id=user_id, email=email, role="admin", plan_tier="pro", currency="USD")
    db.add(user)
    db.flush()
    db.add(CreditBalance(user_id=user_id))
    db.commit()
    db.refresh(user)
    return user


def make_provider(
    db,
    provider_name: str,
    is_primary: bool = False,
    is_fallback: bool = False,
    is_enabled: bool = True,
    model_id: str = "test-model",
):
    """Create a ProviderConfig row."""
    p = ProviderConfig(
        provider_name=provider_name,
        is_primary=is_primary,
        is_fallback=is_fallback,
        is_enabled=is_enabled,
        model_id=model_id,
        api_key_last4="1234",
        api_key_set=True,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ─── list_providers ───────────────────────────────────────────────────────────


class TestListProviders:
    def test_returns_existing_providers(self, db):
        make_provider(db, "gemini", is_primary=True)
        make_provider(db, "anthropic", is_fallback=True)

        result = AdminProviderService.list_providers(db)

        assert len(result) == 2
        names = {p.provider_name for p in result}
        assert names == {"gemini", "anthropic"}

    def test_seeds_defaults_when_empty(self, db):
        """list_providers creates 3 default providers when the table is empty."""
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                GEMINI_API_KEY="test-gemini-key",
                ANTHROPIC_API_KEY="test-anthropic-key",
                OPENAI_API_KEY="test-openai-key",
            )
            result = AdminProviderService.list_providers(db)

        assert len(result) == 3
        names = {p.provider_name for p in result}
        assert names == {"gemini", "anthropic", "openai"}

    def test_seeds_once_not_twice(self, db):
        """Calling list_providers twice should NOT create duplicate rows."""
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                GEMINI_API_KEY="gemini-key",
                ANTHROPIC_API_KEY="anthropic-key",
                OPENAI_API_KEY="openai-key",
            )
            AdminProviderService.list_providers(db)
            result = AdminProviderService.list_providers(db)

        assert len(result) == 3



# ─── update_provider ─────────────────────────────────────────────────────────


class TestUpdateProvider:
    def test_enable_disabled_provider(self, db):
        admin = make_admin(db)
        make_provider(db, "openai", is_enabled=False, model_id="gpt-4o")

        result = AdminProviderService.update_provider(
            db, "openai", admin, is_enabled=True
        )

        assert result.is_enabled is True

    def test_disable_enabled_provider(self, db):
        admin = make_admin(db, user_id="adm-prov-dis")
        make_provider(db, "anthropic", is_enabled=True)

        result = AdminProviderService.update_provider(
            db, "anthropic", admin, is_enabled=False
        )

        assert result.is_enabled is False

    def test_update_model_id(self, db):
        admin = make_admin(db, user_id="adm-prov-model")
        make_provider(db, "gemini", model_id="gemini-2.5-flash")

        result = AdminProviderService.update_provider(
            db, "gemini", admin, model_id="gemini-2.0-flash"
        )

        assert result.model_id == "gemini-2.0-flash"

    def test_update_both_fields(self, db):
        admin = make_admin(db, user_id="adm-prov-both")
        make_provider(db, "openai", is_enabled=False, model_id="gpt-4o")

        result = AdminProviderService.update_provider(
            db, "openai", admin, is_enabled=True, model_id="gpt-4-turbo"
        )

        assert result.is_enabled is True
        assert result.model_id == "gpt-4-turbo"

    def test_update_creates_audit_log(self, db):
        admin = make_admin(db, user_id="adm-prov-audit")
        make_provider(db, "gemini", is_enabled=True)

        result = AdminProviderService.update_provider(
            db, "gemini", admin, is_enabled=False
        )

        log = db.execute(
            select(AdminAuditLog).where(AdminAuditLog.resource_id == result.id)
        ).scalar_one_or_none()
        assert log is not None
        assert log.action == "provider_updated"
        assert log.admin_user_id == admin.id

    def test_update_nonexistent_provider_raises(self, db):
        admin = make_admin(db, user_id="adm-prov-noex")

        with pytest.raises(ResourceNotFoundError, match="not found"):
            AdminProviderService.update_provider(
                db, "nonexistent_provider", admin, is_enabled=True
            )

    def test_update_without_changes_still_persists(self, db):
        """Calling update with no field changes still commits and refreshes."""
        admin = make_admin(db, user_id="adm-prov-noop")
        p = make_provider(db, "gemini", model_id="gemini-2.5-flash", is_enabled=True)

        result = AdminProviderService.update_provider(
            db, "gemini", admin
            # No is_enabled or model_id passed
        )

        assert result.model_id == "gemini-2.5-flash"
        assert result.is_enabled is True


# ─── set_primary_provider ─────────────────────────────────────────────────────


class TestSetPrimaryProvider:
    def test_sets_target_as_primary(self, db):
        admin = make_admin(db, user_id="adm-prim-1")
        make_provider(db, "gemini", is_primary=True)
        make_provider(db, "anthropic", is_primary=False)

        result = AdminProviderService.set_primary_provider(db, "anthropic", admin)

        assert result.is_primary is True

    def test_previous_primary_is_unset(self, db):
        admin = make_admin(db, user_id="adm-prim-2")
        make_provider(db, "gemini", is_primary=True)
        make_provider(db, "openai", is_primary=False)

        AdminProviderService.set_primary_provider(db, "openai", admin)

        db.expire_all()
        gemini = db.scalar(
            select(ProviderConfig).where(ProviderConfig.provider_name == "gemini")
        )
        assert gemini.is_primary is False

    def test_only_one_provider_is_primary_after_switch(self, db):
        admin = make_admin(db, user_id="adm-prim-3")
        make_provider(db, "gemini", is_primary=True)
        make_provider(db, "anthropic", is_primary=False)
        make_provider(db, "openai", is_primary=False)

        AdminProviderService.set_primary_provider(db, "anthropic", admin)

        db.expire_all()
        all_providers = list(db.scalars(select(ProviderConfig)).all())
        primary_count = sum(1 for p in all_providers if p.is_primary)
        assert primary_count == 1

    def test_set_primary_enables_provider(self, db):
        """Setting a disabled provider as primary should enable it."""
        admin = make_admin(db, user_id="adm-prim-4")
        make_provider(db, "gemini", is_primary=True, is_enabled=True)
        make_provider(db, "openai", is_primary=False, is_enabled=False)

        result = AdminProviderService.set_primary_provider(db, "openai", admin)

        assert result.is_enabled is True

    def test_set_primary_creates_audit_log(self, db):
        admin = make_admin(db, user_id="adm-prim-5")
        make_provider(db, "gemini", is_primary=True)
        make_provider(db, "anthropic", is_primary=False)

        result = AdminProviderService.set_primary_provider(db, "anthropic", admin)

        log = db.execute(
            select(AdminAuditLog).where(AdminAuditLog.resource_id == result.id)
        ).scalar_one_or_none()
        assert log is not None
        assert log.action == "provider_primary_changed"
        assert "anthropic" in log.description

    def test_set_primary_nonexistent_provider_raises(self, db):
        admin = make_admin(db, user_id="adm-prim-6")

        with pytest.raises(ResourceNotFoundError, match="not found"):
            AdminProviderService.set_primary_provider(db, "does_not_exist", admin)

    def test_set_primary_when_no_current_primary(self, db):
        """Edge case: no provider is currently primary."""
        admin = make_admin(db, user_id="adm-prim-7")
        make_provider(db, "gemini", is_primary=False)

        result = AdminProviderService.set_primary_provider(db, "gemini", admin)

        assert result.is_primary is True

    def test_set_primary_self_is_idempotent(self, db):
        """Setting current primary as primary again should still work."""
        admin = make_admin(db, user_id="adm-prim-8")
        make_provider(db, "gemini", is_primary=True)

        result = AdminProviderService.set_primary_provider(db, "gemini", admin)

        assert result.is_primary is True


# ─── set_api_key ──────────────────────────────────────────────────────────────


class TestSetApiKey:
    @patch("app.llm.provider.get_provider")
    def test_stores_last4_in_db(self, mock_get_provider, db, tmp_path):
        mock_get_provider.cache_clear = MagicMock()
        admin = make_admin(db, user_id="adm-key-1")
        make_provider(db, "gemini")

        env_file = tmp_path / ".env"
        env_file.write_text("GEMINI_API_KEY=old_key\n")

        with patch("os.path.exists", return_value=False), \
             patch("os.replace"), \
             patch("builtins.open", MagicMock()):
            result = AdminProviderService.set_api_key(
                db, "gemini", "newkey-abcd1234", admin
            )

        assert result.api_key_last4 == "1234"
        assert result.api_key_set is True

    @patch("app.llm.provider.get_provider")
    def test_valid_key_alphanumeric(self, mock_get_provider, db):
        mock_get_provider.cache_clear = MagicMock()
        admin = make_admin(db, user_id="adm-key-2")
        make_provider(db, "anthropic")

        with patch("os.path.exists", return_value=False), \
             patch("os.replace"), \
             patch("builtins.open", MagicMock()):
            result = AdminProviderService.set_api_key(
                db, "anthropic", "sk-ant-api03-valid123", admin
            )

        assert result.api_key_set is True

    def test_invalid_key_with_spaces_raises(self, db):
        admin = make_admin(db, user_id="adm-key-3")
        make_provider(db, "openai")

        with pytest.raises(InvalidStateError, match="invalid characters"):
            AdminProviderService.set_api_key(
                db, "openai", "key with spaces", admin
            )

    def test_invalid_key_with_newline_raises(self, db):
        admin = make_admin(db, user_id="adm-key-4")
        make_provider(db, "openai")

        with pytest.raises(InvalidStateError, match="invalid characters"):
            AdminProviderService.set_api_key(
                db, "openai", "key\ninjection", admin
            )

    def test_invalid_key_with_semicolon_raises(self, db):
        admin = make_admin(db, user_id="adm-key-5")
        make_provider(db, "openai")

        with pytest.raises(InvalidStateError, match="invalid characters"):
            AdminProviderService.set_api_key(
                db, "openai", "key;rm -rf /", admin
            )

    def test_set_api_key_nonexistent_provider_raises(self, db):
        admin = make_admin(db, user_id="adm-key-6")

        with pytest.raises(ResourceNotFoundError, match="not found"):
            AdminProviderService.set_api_key(
                db, "no_such_provider", "valid-key-1234", admin
            )

    @patch("app.llm.provider.get_provider")
    def test_set_api_key_creates_audit_log(self, mock_get_provider, db):
        mock_get_provider.cache_clear = MagicMock()
        admin = make_admin(db, user_id="adm-key-7")
        p = make_provider(db, "gemini")

        with patch("os.path.exists", return_value=False), \
             patch("os.replace"), \
             patch("builtins.open", MagicMock()):
            result = AdminProviderService.set_api_key(
                db, "gemini", "newkey-xyz9", admin
            )

        log = db.execute(
            select(AdminAuditLog).where(AdminAuditLog.resource_id == result.id)
        ).scalar_one_or_none()
        assert log is not None
        assert log.action == "api_key_updated"
        # The actual key must NOT appear in audit log description
        assert "newkey-xyz9" not in (log.description or "")

    @patch("app.llm.provider.get_provider")
    def test_short_key_stores_full_key_as_last4(self, mock_get_provider, db):
        """Keys shorter than 4 chars use the full key as last4."""
        mock_get_provider.cache_clear = MagicMock()
        admin = make_admin(db, user_id="adm-key-8")
        make_provider(db, "openai")

        with patch("os.path.exists", return_value=False), \
             patch("os.replace"), \
             patch("builtins.open", MagicMock()):
            result = AdminProviderService.set_api_key(
                db, "openai", "abc", admin
            )

        # len("abc") < 4, so last4 == "abc" itself
        assert result.api_key_last4 == "abc"

    @patch("app.llm.provider.get_provider")
    def test_lru_cache_cleared_after_key_update(self, mock_get_provider, db):
        mock_get_provider.cache_clear = MagicMock()
        admin = make_admin(db, user_id="adm-key-9")
        make_provider(db, "gemini")

        with patch("os.path.exists", return_value=False), \
             patch("os.replace"), \
             patch("builtins.open", MagicMock()):
            AdminProviderService.set_api_key(
                db, "gemini", "freshkey-1234", admin
            )

        mock_get_provider.cache_clear.assert_called_once()

    @patch("app.llm.provider.get_provider")
    def test_dots_and_hyphens_in_key_are_valid(self, mock_get_provider, db):
        """Keys containing dots and hyphens (common in real API keys) should pass validation."""
        mock_get_provider.cache_clear = MagicMock()
        admin = make_admin(db, user_id="adm-key-10")
        make_provider(db, "anthropic")

        with patch("os.path.exists", return_value=False), \
             patch("os.replace"), \
             patch("builtins.open", MagicMock()):
            result = AdminProviderService.set_api_key(
                db, "anthropic", "sk-ant-api03-abc.xyz-1234", admin
            )

        assert result.api_key_set is True
