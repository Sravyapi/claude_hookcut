"""AdminProviderService — LLM provider configuration management."""

import logging
import os
import re
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.admin import ProviderConfig
from app.exceptions import ResourceNotFoundError, InvalidStateError

logger = logging.getLogger(__name__)


class AdminProviderService:
    """All methods are static — no instance state required."""

    @staticmethod
    def list_providers(db: Session) -> list[ProviderConfig]:
        """All provider configs. Seeds defaults if none exist."""
        providers = list(
            db.scalars(select(ProviderConfig)).all()
        )
        if providers:
            return providers

        # Seed defaults
        from app.config import get_settings

        settings = get_settings()

        defaults = [
            ProviderConfig(
                provider_name="gemini",
                is_primary=True,
                is_fallback=False,
                is_enabled=True,
                model_id="gemini-2.5-flash",
                api_key_last4=settings.GEMINI_API_KEY[-4:]
                if settings.GEMINI_API_KEY
                else "",
                api_key_set=bool(settings.GEMINI_API_KEY),
            ),
            ProviderConfig(
                provider_name="anthropic",
                is_primary=False,
                is_fallback=True,
                is_enabled=True,
                model_id="claude-sonnet-4-20250514",
                api_key_last4=settings.ANTHROPIC_API_KEY[-4:]
                if settings.ANTHROPIC_API_KEY
                else "",
                api_key_set=bool(settings.ANTHROPIC_API_KEY),
            ),
            ProviderConfig(
                provider_name="openai",
                is_primary=False,
                is_fallback=False,
                is_enabled=False,
                model_id="gpt-4o",
                api_key_last4=settings.OPENAI_API_KEY[-4:]
                if settings.OPENAI_API_KEY
                else "",
                api_key_set=bool(settings.OPENAI_API_KEY),
            ),
        ]
        for p in defaults:
            db.add(p)
        db.commit()
        for p in defaults:
            db.refresh(p)
        return defaults

    @staticmethod
    def update_provider(
        db: Session,
        provider_name: str,
        admin_user: User,
        is_enabled: bool | None = None,
        model_id: str | None = None,
    ) -> ProviderConfig:
        """Update provider config fields and create audit log."""
        provider = db.scalar(
            select(ProviderConfig).where(
                ProviderConfig.provider_name == provider_name
            )
        )
        if not provider:
            raise ResourceNotFoundError(
                f"Provider {provider_name} not found"
            )

        before_state = {
            "is_enabled": provider.is_enabled,
            "model_id": provider.model_id,
        }

        if is_enabled is not None:
            provider.is_enabled = is_enabled
        if model_id is not None:
            provider.model_id = model_id

        after_state = {
            "is_enabled": provider.is_enabled,
            "model_id": provider.model_id,
        }
        provider.updated_by = admin_user.id

        from app.services.admin_service import AdminService
        AdminService.create_audit_log(
            db,
            admin_user=admin_user,
            action="provider_updated",
            resource_type="provider_config",
            resource_id=provider.id,
            before_state=before_state,
            after_state=after_state,
            description=f"Updated provider {provider_name}",
        )
        db.commit()
        db.refresh(provider)
        return provider

    @staticmethod
    def set_primary_provider(
        db: Session, provider_name: str, admin_user: User
    ) -> ProviderConfig:
        """Set one provider as primary, unsetting all others."""
        target = db.scalar(
            select(ProviderConfig).where(
                ProviderConfig.provider_name == provider_name
            )
        )
        if not target:
            raise ResourceNotFoundError(
                f"Provider {provider_name} not found"
            )

        # Find current primary for audit trail
        current_primary = db.scalar(
            select(ProviderConfig).where(
                ProviderConfig.is_primary == True  # noqa: E712
            )
        )
        before_primary = (
            current_primary.provider_name if current_primary else None
        )

        # Unset all is_primary; set updated_at explicitly since onupdate only
        # fires for ORM-level updates, not bulk db.execute(update(...)) calls.
        db.execute(
            update(ProviderConfig).values(is_primary=False, updated_at=datetime.now(timezone.utc))
        )

        target.is_primary = True
        target.is_enabled = True
        target.updated_by = admin_user.id

        from app.services.admin_service import AdminService
        AdminService.create_audit_log(
            db,
            admin_user=admin_user,
            action="provider_primary_changed",
            resource_type="provider_config",
            resource_id=target.id,
            before_state={"primary_provider": before_primary},
            after_state={"primary_provider": provider_name},
            description=(
                f"Changed primary provider from "
                f"{before_primary} to {provider_name}"
            ),
        )
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def set_api_key(
        db: Session,
        provider_name: str,
        api_key: str,
        admin_user: User,
    ) -> ProviderConfig:
        """
        Store last4 in DB and write the actual key to the .env file.
        Never logs the actual key -- only the last 4 characters.
        """
        if not re.match(r'^[A-Za-z0-9_\-\.]+$', api_key):
            raise InvalidStateError("API key contains invalid characters")

        provider = db.scalar(
            select(ProviderConfig).where(
                ProviderConfig.provider_name == provider_name
            )
        )
        if not provider:
            raise ResourceNotFoundError(
                f"Provider {provider_name} not found"
            )

        last4 = api_key[-4:] if len(api_key) >= 4 else api_key
        provider.api_key_last4 = last4
        provider.api_key_set = True
        provider.updated_by = admin_user.id

        # Map provider name to .env variable
        env_var_map = {
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
        }
        env_var = env_var_map.get(provider_name)

        if env_var:
            from pathlib import Path
            env_path = (Path(__file__).parent.parent.parent / ".env").resolve()
            project_root = Path(__file__).parent.parent.parent.resolve()
            if not str(env_path).startswith(str(project_root)):
                raise ValueError("Invalid .env path")
            env_path = str(env_path)
            try:
                if os.path.exists(env_path):
                    with open(env_path, "r") as f:
                        lines = f.readlines()

                    found = False
                    new_lines = []
                    for line in lines:
                        if line.strip().startswith(f"{env_var}="):
                            new_lines.append(f"{env_var}={api_key}\n")
                            found = True
                        else:
                            new_lines.append(line)

                    if not found:
                        new_lines.append(f"{env_var}={api_key}\n")

                    tmp_path = env_path + ".tmp"
                    with open(tmp_path, "w") as f:
                        f.writelines(new_lines)
                    os.replace(tmp_path, env_path)  # atomic on POSIX
                else:
                    tmp_path = env_path + ".tmp"
                    with open(tmp_path, "w") as f:
                        f.write(f"{env_var}={api_key}\n")
                    os.replace(tmp_path, env_path)  # atomic on POSIX
            except OSError as e:
                logger.error("Failed to write API key to .env: %s", e)

        # Clear the LRU cache so the next get_provider() call picks up the new key
        from app.llm.provider import get_provider
        get_provider.cache_clear()

        from app.services.admin_service import AdminService
        AdminService.create_audit_log(
            db,
            admin_user=admin_user,
            action="api_key_updated",
            resource_type="provider_config",
            resource_id=provider.id,
            before_state={"api_key_last4": provider.api_key_last4},
            after_state={"api_key_last4": last4, "api_key_set": True},
            description=(
                f"Updated API key for {provider_name} (****{last4})"
            ),
        )
        db.commit()
        db.refresh(provider)
        return provider
