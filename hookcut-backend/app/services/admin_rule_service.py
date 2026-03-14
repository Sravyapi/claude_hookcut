"""AdminRuleService — prompt rule CRUD with versioning."""

import logging

from sqlalchemy import func, select, desc, and_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.admin import PromptRule
from app.exceptions import ResourceNotFoundError, HookCutError
from app.llm.prompts.constants import BASE_HOOK_RULES as BASE_RULES

logger = logging.getLogger(__name__)


class AdminRuleService:
    """All methods are static — no instance state required."""

    @staticmethod
    def list_rules(db: Session) -> list[PromptRule]:
        """All active rules (latest version per rule_key), ordered by rule_key."""
        try:
            # Subquery: max version per rule_key where is_active=True
            max_version_sub = (
                select(
                    PromptRule.rule_key,
                    func.max(PromptRule.version).label("max_ver"),
                )
                .where(PromptRule.is_active == True)  # noqa: E712
                .group_by(PromptRule.rule_key)
                .subquery()
            )

            stmt = (
                select(PromptRule)
                .join(
                    max_version_sub,
                    and_(
                        PromptRule.rule_key == max_version_sub.c.rule_key,
                        PromptRule.version == max_version_sub.c.max_ver,
                    ),
                )
                .order_by(PromptRule.rule_key)
            )
            return list(db.scalars(stmt).all())
        except Exception as e:
            logger.exception("Failed to list rules")
            raise HookCutError(f"List rules error: {e}") from e

    @staticmethod
    def get_active_rules_as_dicts(db: Session) -> list[dict]:
        """Get active rules as plain dicts for prompt building.
        Returns list of {'rule_key': str, 'content': str} dicts."""
        rules = AdminRuleService.list_rules(db)
        return [{"rule_key": r.rule_key, "content": r.content} for r in rules]

    @staticmethod
    def create_rule(
        db: Session,
        title: str,
        content: str,
        rule_key: str | None,
        admin_user: User,
    ) -> PromptRule:
        """Create a custom prompt rule. Auto-assigns key after Q if not provided."""
        try:
            if not rule_key:
                # Find the highest existing key using integer-aware comparison
                # to avoid lexicographic bugs (e.g. "Z2" > "Z10")
                all_keys = list(
                    db.scalars(select(PromptRule.rule_key)).all()
                )
                # Partition into single-letter keys (A-Z) and Z{N} extended keys
                single_letter_keys = [k for k in all_keys if len(k) == 1 and k.isalpha()]
                extended_keys = [k for k in all_keys if len(k) > 1 and k[0] == "Z" and k[1:].isdigit()]

                if extended_keys:
                    max_num = max(int(k[1:]) for k in extended_keys)
                    rule_key = f"Z{max_num + 1}"
                elif single_letter_keys:
                    max_letter = max(single_letter_keys, key=lambda k: ord(k.upper()))
                    next_ord = ord(max_letter.upper()) + 1
                    rule_key = chr(next_ord) if next_ord <= ord("Z") else "Z1"
                else:
                    rule_key = "R"

            rule = PromptRule(
                rule_key=rule_key,
                version=1,
                title=title,
                content=content,
                is_base_rule=False,
                is_active=True,
                created_by=admin_user.id,
            )
            db.add(rule)
            db.flush()

            from app.services.admin_service import AdminService
            AdminService.create_audit_log(
                db,
                admin_user=admin_user,
                action="prompt_rule_created",
                resource_type="prompt_rule",
                resource_id=rule.id,
                before_state=None,
                after_state={"rule_key": rule_key, "title": title},
                description=f"Created custom rule {rule_key}: {title}",
            )
            db.commit()
            db.refresh(rule)
            return rule
        except HookCutError:
            raise
        except Exception as e:
            db.rollback()
            logger.exception("Failed to create rule")
            raise HookCutError(f"Create rule error: {e}") from e

    @staticmethod
    def update_rule(
        db: Session,
        rule_id: str,
        admin_user: User,
        title: str | None = None,
        content: str | None = None,
        is_active: bool | None = None,
    ) -> PromptRule:
        """
        Create a NEW version of the rule (don't edit in place).
        Copy existing fields, apply updates, increment version,
        set parent_version_id, deactivate old version.
        """
        old_rule = db.get(PromptRule, rule_id)
        if not old_rule:
            raise ResourceNotFoundError(f"Rule {rule_id} not found")

        before_state = {
            "rule_key": old_rule.rule_key,
            "version": old_rule.version,
            "title": old_rule.title,
            "content": old_rule.content,
            "is_active": old_rule.is_active,
        }

        new_rule = PromptRule(
            rule_key=old_rule.rule_key,
            version=old_rule.version + 1,
            title=title if title is not None else old_rule.title,
            content=content if content is not None else old_rule.content,
            is_base_rule=old_rule.is_base_rule,
            is_active=is_active if is_active is not None else True,
            parent_version_id=old_rule.id,
            created_by=admin_user.id,
        )

        # Deactivate the old version
        old_rule.is_active = False

        db.add(new_rule)
        db.flush()

        after_state = {
            "rule_key": new_rule.rule_key,
            "version": new_rule.version,
            "title": new_rule.title,
            "content": new_rule.content,
            "is_active": new_rule.is_active,
        }

        from app.services.admin_service import AdminService
        AdminService.create_audit_log(
            db,
            admin_user=admin_user,
            action="prompt_rule_updated",
            resource_type="prompt_rule",
            resource_id=new_rule.id,
            before_state=before_state,
            after_state=after_state,
            description=(
                f"Updated rule {new_rule.rule_key} "
                f"v{old_rule.version} -> v{new_rule.version}"
            ),
        )
        db.commit()
        db.refresh(new_rule)
        return new_rule

    @staticmethod
    def revert_rule(
        db: Session,
        rule_id: str,
        target_version_id: str,
        admin_user: User,
    ) -> PromptRule:
        """Create new version copying content from target version."""
        current_rule = db.get(PromptRule, rule_id)
        if not current_rule:
            raise ResourceNotFoundError(f"Rule {rule_id} not found")

        target_rule = db.get(PromptRule, target_version_id)
        if not target_rule:
            raise ResourceNotFoundError(
                f"Target version {target_version_id} not found"
            )

        # Get the latest version number for this rule_key
        latest_version = db.scalar(
            select(func.max(PromptRule.version)).where(
                PromptRule.rule_key == current_rule.rule_key
            )
        ) or current_rule.version

        # Deactivate current active version
        current_rule.is_active = False

        new_rule = PromptRule(
            rule_key=current_rule.rule_key,
            version=latest_version + 1,
            title=target_rule.title,
            content=target_rule.content,
            is_base_rule=current_rule.is_base_rule,
            is_active=True,
            parent_version_id=current_rule.id,
            created_by=admin_user.id,
        )
        db.add(new_rule)
        db.flush()

        from app.services.admin_service import AdminService
        AdminService.create_audit_log(
            db,
            admin_user=admin_user,
            action="prompt_rule_reverted",
            resource_type="prompt_rule",
            resource_id=new_rule.id,
            before_state={
                "version": current_rule.version,
                "title": current_rule.title,
            },
            after_state={
                "version": new_rule.version,
                "title": new_rule.title,
                "reverted_from_version_id": target_version_id,
            },
            description=(
                f"Reverted rule {new_rule.rule_key} to content from "
                f"version {target_rule.version}"
            ),
        )
        db.commit()
        db.refresh(new_rule)
        return new_rule

    @staticmethod
    def delete_rule(
        db: Session, rule_id: str, admin_user: User
    ) -> None:
        """Deactivate a custom rule. Base rules cannot be deleted."""
        rule = db.get(PromptRule, rule_id)
        if not rule:
            raise ResourceNotFoundError(f"Rule {rule_id} not found")

        if rule.is_base_rule:
            raise HookCutError("Cannot delete base rules (A-Q)")

        rule.is_active = False

        from app.services.admin_service import AdminService
        AdminService.create_audit_log(
            db,
            admin_user=admin_user,
            action="prompt_rule_deleted",
            resource_type="prompt_rule",
            resource_id=rule_id,
            before_state={"rule_key": rule.rule_key, "is_active": True},
            after_state={"rule_key": rule.rule_key, "is_active": False},
            description=f"Deleted (deactivated) custom rule {rule.rule_key}: {rule.title}",
        )
        db.commit()

    @staticmethod
    def seed_rules(
        db: Session, admin_user: User
    ) -> list[PromptRule]:
        """Seed the 17 base rules A-Q using an upsert pattern (idempotent/resumable)."""
        # Fetch all existing (rule_key, version) pairs to detect what already exists
        existing_pairs = set(
            db.execute(
                select(PromptRule.rule_key, PromptRule.version)
            ).all()
        )

        rules: list[PromptRule] = []
        inserted_keys: list[str] = []
        for key, data in BASE_RULES.items():
            if (key, 1) in existing_pairs:
                # Already seeded — skip to make this call idempotent
                logger.debug("Rule %s v1 already exists, skipping", key)
                continue
            rule = PromptRule(
                rule_key=key,
                version=1,
                title=data["title"],
                content=data["content"],
                is_base_rule=True,
                is_active=True,
                created_by=admin_user.id,
            )
            db.add(rule)
            rules.append(rule)
            inserted_keys.append(key)

        if not rules:
            logger.info("All base rules already exist, nothing to seed")
        else:
            db.flush()
            from app.services.admin_service import AdminService
            AdminService.create_audit_log(
                db,
                admin_user=admin_user,
                action="prompt_rule_created",
                resource_type="prompt_rule",
                resource_id=None,
                before_state=None,
                after_state={"rules_seeded": inserted_keys},
                description=f"Seeded {len(inserted_keys)} base rules ({', '.join(inserted_keys)})",
            )
            db.commit()
            for rule in rules:
                db.refresh(rule)
            logger.info("Seeded %d base rules: %s", len(inserted_keys), inserted_keys)

        # Return all active rules regardless of what was just inserted
        return list(
            db.scalars(
                select(PromptRule)
                .where(PromptRule.is_active == True)  # noqa: E712
                .order_by(PromptRule.rule_key)
            ).all()
        )

    @staticmethod
    def preview_prompt(
        db: Session, niche: str, language: str
    ) -> dict:
        """Build prompt using active DB rules. Falls back to hardcoded prompt."""
        try:
            from app.llm.prompts.hook_identification import build_hook_prompt_from_rules

            rules = AdminRuleService.get_active_rules_as_dicts(db)
            prompt_text = build_hook_prompt_from_rules(
                rules=rules,
                niche=niche,
                transcript="[PREVIEW — no transcript]",
                language=language,
            )
            return {
                "prompt_text": prompt_text,
                "rule_count": len(rules),
                "character_count": len(prompt_text),
            }
        except Exception as e:
            logger.exception("Failed to preview prompt")
            raise HookCutError(f"Preview prompt error: {e}") from e

    @staticmethod
    def get_rule_history(
        db: Session, rule_key: str
    ) -> list[PromptRule]:
        """All versions for a rule_key, ordered by version desc."""
        stmt = (
            select(PromptRule)
            .where(PromptRule.rule_key == rule_key)
            .order_by(desc(PromptRule.version))
        )
        return list(db.scalars(stmt).all())
