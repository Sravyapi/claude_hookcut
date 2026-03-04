"""
AdminService — business logic for the admin dashboard.

Covers: dashboard stats, user management, session browsing, audit logs,
prompt rule CRUD with versioning, LLM provider configuration, and
NARM (Niche-Aware Recommendation Model) insight generation.
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, desc, and_, update
from sqlalchemy.orm import Session

from app.models.user import User, Subscription
from app.models.session import AnalysisSession, Hook, Short
from app.models.learning import LearningLog
from app.models.admin import AdminAuditLog, PromptRule, ProviderConfig, NarmInsight
from app.exceptions import ResourceNotFoundError, HookCutError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Seed data: the 17 base rules (A-Q) extracted from the hardcoded prompt
# ---------------------------------------------------------------------------
BASE_RULES: dict[str, dict[str, str]] = {
    "A": {
        "title": "One topic per hook",
        "content": "One topic per hook \u2014 3+ topics = FAIL",
    },
    "B": {
        "title": "Contextual grounding",
        "content": (
            "Contextual grounding \u2014 viewer must know WHO and WHY immediately"
        ),
    },
    "C": {
        "title": "Specificity serves one point only",
        "content": "Specificity serves one point only",
    },
    "D": {
        "title": "Character + proof arc",
        "content": (
            "Character + proof arc (person + achievement in tight sequence)"
        ),
    },
    "E": {
        "title": "Let hook breathe",
        "content": (
            "Let hook breathe \u2014 include follow-up sentences that complete the thought"
        ),
    },
    "F": {
        "title": "Urgency/FOMO framing",
        "content": 'Urgency/FOMO framing ("while you were sleeping...")',
    },
    "G": {
        "title": "No generic claims without specific proof",
        "content": "No generic claims without specific proof",
    },
    "H": {
        "title": "Narrative escalation",
        "content": (
            "Narrative escalation: "
            "intrigue\u2192proof\u2192escalation\u2192contrast\u2192open loop"
        ),
    },
    "I": {
        "title": "Composite hooks",
        "content": (
            "Composite hooks: stitch non-contiguous segments for stronger arcs"
        ),
    },
    "J": {
        "title": "End at the landing",
        "content": "End at the landing \u2014 not before, not after",
    },
    "K": {
        "title": "Unresolved mechanism",
        "content": "Unresolved mechanism: viewer knows WHAT not HOW",
    },
    "L": {
        "title": "Pain escalation",
        "content": (
            "Pain escalation: layer frustration "
            "(statement\u2192specifics\u2192vivid analogy)"
        ),
    },
    "M": {
        "title": "Elimination hooks",
        "content": "Elimination hooks: remove expected answers systematically",
    },
    "N": {
        "title": "Objection handling",
        "content": "Objection handling: catch viewers at bounce moment",
    },
    "O": {
        "title": "Funnel role diversity",
        "content": "Funnel role diversity: 5 hooks serve different purposes",
    },
    "P": {
        "title": "Strip section labels",
        "content": "Strip section labels/navigation text from hook starts",
    },
    "Q": {
        "title": "Workflow demos",
        "content": (
            "Workflow demos: include full step-by-step sequence, "
            "don't cut mid-demo"
        ),
    },
}


class AdminService:
    """All methods are static \u2014 no instance state required."""

    # ------------------------------------------------------------------
    # 1. Dashboard stats
    # ------------------------------------------------------------------
    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        """Aggregate counts and last 10 sessions with user email."""
        try:
            total_users = db.scalar(select(func.count(User.id))) or 0
            total_sessions = db.scalar(
                select(func.count(AnalysisSession.id))
            ) or 0
            total_shorts = db.scalar(select(func.count(Short.id))) or 0
            active_subs = db.scalar(
                select(func.count(Subscription.id)).where(
                    Subscription.status == "active"
                )
            ) or 0

            recent_stmt = (
                select(AnalysisSession, User.email)
                .join(User, AnalysisSession.user_id == User.id)
                .order_by(desc(AnalysisSession.created_at))
                .limit(10)
            )
            recent_rows = db.execute(recent_stmt).all()
            recent_sessions = [
                {
                    "id": s.id,
                    "user_email": email,
                    "video_title": s.video_title,
                    "video_id": s.video_id,
                    "status": s.status,
                    "niche": s.niche,
                    "minutes_charged": s.minutes_charged,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s, email in recent_rows
            ]

            return {
                "total_users": total_users,
                "total_sessions": total_sessions,
                "total_shorts": total_shorts,
                "active_subscriptions": active_subs,
                "recent_sessions": recent_sessions,
            }
        except Exception as e:
            logger.exception("Failed to fetch dashboard stats")
            raise HookCutError(f"Dashboard stats error: {e}") from e

    # ------------------------------------------------------------------
    # 2. Paginated user list
    # ------------------------------------------------------------------
    @staticmethod
    def list_users(
        db: Session, page: int = 1, per_page: int = 20
    ) -> dict:
        """Return paginated users with per-user session counts."""
        try:
            total = db.scalar(select(func.count(User.id))) or 0

            session_count_sub = (
                select(
                    AnalysisSession.user_id,
                    func.count(AnalysisSession.id).label("session_count"),
                )
                .group_by(AnalysisSession.user_id)
                .subquery()
            )

            stmt = (
                select(User, session_count_sub.c.session_count)
                .outerjoin(
                    session_count_sub,
                    User.id == session_count_sub.c.user_id,
                )
                .order_by(desc(User.created_at))
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            rows = db.execute(stmt).all()

            users = [
                {
                    "id": u.id,
                    "email": u.email,
                    "role": u.role,
                    "plan_tier": u.plan_tier,
                    "currency": u.currency,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "session_count": count or 0,
                }
                for u, count in rows
            ]

            return {
                "users": users,
                "total": total,
                "page": page,
                "per_page": per_page,
            }
        except Exception as e:
            logger.exception("Failed to list users")
            raise HookCutError(f"List users error: {e}") from e

    # ------------------------------------------------------------------
    # 3. Update user role
    # ------------------------------------------------------------------
    @staticmethod
    def update_user_role(
        db: Session, user_id: str, new_role: str, admin_user: User
    ) -> User:
        """Change a user's role and record an audit log."""
        user = db.get(User, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        before = {"role": user.role}
        user.role = new_role
        after = {"role": new_role}

        AdminService.create_audit_log(
            db,
            admin_user=admin_user,
            action="role_changed",
            resource_type="user",
            resource_id=user_id,
            before_state=before,
            after_state=after,
            description=f"Changed role from {before['role']} to {new_role}",
        )
        db.commit()
        db.refresh(user)
        return user

    # ------------------------------------------------------------------
    # 4. Paginated sessions (all users)
    # ------------------------------------------------------------------
    @staticmethod
    def list_all_sessions(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
    ) -> dict:
        """Paginated analysis sessions with user email. Optional status filter."""
        try:
            count_stmt = select(func.count(AnalysisSession.id))
            list_stmt = (
                select(AnalysisSession, User.email)
                .join(User, AnalysisSession.user_id == User.id)
            )

            if status:
                count_stmt = count_stmt.where(AnalysisSession.status == status)
                list_stmt = list_stmt.where(AnalysisSession.status == status)

            total = db.scalar(count_stmt) or 0

            list_stmt = (
                list_stmt.order_by(desc(AnalysisSession.created_at))
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            rows = db.execute(list_stmt).all()

            sessions = [
                {
                    "id": s.id,
                    "user_email": email,
                    "video_title": s.video_title,
                    "video_id": s.video_id,
                    "niche": s.niche,
                    "status": s.status,
                    "minutes_charged": s.minutes_charged,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s, email in rows
            ]

            return {
                "sessions": sessions,
                "total": total,
                "page": page,
                "per_page": per_page,
            }
        except Exception as e:
            logger.exception("Failed to list sessions")
            raise HookCutError(f"List sessions error: {e}") from e

    # ------------------------------------------------------------------
    # 5. Session detail
    # ------------------------------------------------------------------
    @staticmethod
    def get_session_detail(db: Session, session_id: str) -> dict:
        """Full session with hooks, shorts, and user email."""
        row = db.execute(
            select(AnalysisSession, User.email)
            .join(User, AnalysisSession.user_id == User.id)
            .where(AnalysisSession.id == session_id)
        ).first()

        if not row:
            raise ResourceNotFoundError(f"Session {session_id} not found")

        session, user_email = row

        hooks = [
            {
                "id": h.id,
                "rank": h.rank,
                "hook_text": h.hook_text,
                "start_time": h.start_time,
                "end_time": h.end_time,
                "hook_type": h.hook_type,
                "funnel_role": h.funnel_role,
                "scores": h.scores,
                "attention_score": h.attention_score,
                "platform_dynamics": h.platform_dynamics,
                "viewer_psychology": h.viewer_psychology,
                "improvement_suggestion": h.improvement_suggestion,
                "is_composite": h.is_composite,
                "is_selected": h.is_selected,
            }
            for h in session.hooks
        ]

        shorts = [
            {
                "id": sh.id,
                "hook_id": sh.hook_id,
                "status": sh.status,
                "caption_style": sh.caption_style,
                "title": sh.title,
                "download_url": sh.download_url,
                "duration_seconds": sh.duration_seconds,
                "file_size_bytes": sh.file_size_bytes,
            }
            for sh in session.shorts
        ]

        return {
            "id": session.id,
            "user_id": session.user_id,
            "user_email": user_email,
            "youtube_url": session.youtube_url,
            "video_id": session.video_id,
            "video_title": session.video_title,
            "video_duration_seconds": session.video_duration_seconds,
            "niche": session.niche,
            "language": session.language,
            "status": session.status,
            "transcript_provider": session.transcript_provider,
            "minutes_charged": session.minutes_charged,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "hooks": hooks,
            "shorts": shorts,
        }

    # ------------------------------------------------------------------
    # 6. Paginated audit logs
    # ------------------------------------------------------------------
    @staticmethod
    def list_audit_logs(
        db: Session,
        page: int = 1,
        per_page: int = 20,
        action: str | None = None,
    ) -> dict:
        """Paginated audit logs with admin email. Optional action filter."""
        try:
            count_stmt = select(func.count(AdminAuditLog.id))
            list_stmt = (
                select(AdminAuditLog, User.email)
                .join(User, AdminAuditLog.admin_user_id == User.id)
            )

            if action:
                count_stmt = count_stmt.where(AdminAuditLog.action == action)
                list_stmt = list_stmt.where(AdminAuditLog.action == action)

            total = db.scalar(count_stmt) or 0

            list_stmt = (
                list_stmt.order_by(desc(AdminAuditLog.created_at))
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            rows = db.execute(list_stmt).all()

            logs = [
                {
                    "id": log.id,
                    "admin_user_id": log.admin_user_id,
                    "admin_email": email,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "before_state": log.before_state,
                    "after_state": log.after_state,
                    "description": log.description,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log, email in rows
            ]

            return {
                "logs": logs,
                "total": total,
                "page": page,
                "per_page": per_page,
            }
        except Exception as e:
            logger.exception("Failed to list audit logs")
            raise HookCutError(f"List audit logs error: {e}") from e

    # ------------------------------------------------------------------
    # 7. Export audit logs
    # ------------------------------------------------------------------
    @staticmethod
    def export_audit_logs(
        db: Session,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """All audit logs in date range as list of dicts."""
        try:
            stmt = (
                select(AdminAuditLog, User.email)
                .join(User, AdminAuditLog.admin_user_id == User.id)
            )

            if start_date:
                start_dt = datetime.fromisoformat(start_date).replace(
                    tzinfo=timezone.utc
                )
                stmt = stmt.where(AdminAuditLog.created_at >= start_dt)
            if end_date:
                end_dt = datetime.fromisoformat(end_date).replace(
                    tzinfo=timezone.utc
                )
                stmt = stmt.where(AdminAuditLog.created_at <= end_dt)

            stmt = stmt.order_by(desc(AdminAuditLog.created_at)).limit(10000)
            rows = db.execute(stmt).all()

            return [
                {
                    "id": log.id,
                    "admin_user_id": log.admin_user_id,
                    "admin_email": email,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "before_state": log.before_state,
                    "after_state": log.after_state,
                    "description": log.description,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log, email in rows
            ]
        except Exception as e:
            logger.exception("Failed to export audit logs")
            raise HookCutError(f"Export audit logs error: {e}") from e

    # ------------------------------------------------------------------
    # 8. Create audit log (helper)
    # ------------------------------------------------------------------
    @staticmethod
    def create_audit_log(
        db: Session,
        admin_user: User,
        action: str,
        resource_type: str,
        resource_id: str | None,
        before_state: dict | None,
        after_state: dict | None,
        description: str,
    ) -> AdminAuditLog:
        """Create and flush an audit log entry."""
        log = AdminAuditLog(
            admin_user_id=admin_user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            description=description,
        )
        db.add(log)
        db.flush()
        return log

    # ------------------------------------------------------------------
    # 9. List active rules (latest version per rule_key)
    # ------------------------------------------------------------------
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
        rules = AdminService.list_rules(db)
        return [{"rule_key": r.rule_key, "content": r.content} for r in rules]

    # ------------------------------------------------------------------
    # 10. Create a custom rule
    # ------------------------------------------------------------------
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
                # Find the highest existing key and pick the next letter
                max_key_row = db.scalar(
                    select(func.max(PromptRule.rule_key))
                )
                if max_key_row and len(max_key_row) == 1 and max_key_row.isalpha():
                    next_ord = ord(max_key_row.upper()) + 1
                    rule_key = chr(next_ord) if next_ord <= ord("Z") else f"Z{next_ord - ord('Z')}"
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

    # ------------------------------------------------------------------
    # 11. Update rule (versioned)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 12. Revert rule to a target version
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 13. Delete (deactivate) a custom rule
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 14. Seed base rules A-Q
    # ------------------------------------------------------------------
    @staticmethod
    def seed_rules(
        db: Session, admin_user: User
    ) -> list[PromptRule]:
        """Seed the 17 base rules A-Q if no rules exist yet."""
        existing_count = db.scalar(
            select(func.count(PromptRule.id))
        ) or 0
        if existing_count > 0:
            logger.info(
                "Rules already exist (%d), skipping seed", existing_count
            )
            return list(
                db.scalars(
                    select(PromptRule)
                    .where(PromptRule.is_active == True)  # noqa: E712
                    .order_by(PromptRule.rule_key)
                ).all()
            )

        rules: list[PromptRule] = []
        for key, data in BASE_RULES.items():
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

        db.flush()

        AdminService.create_audit_log(
            db,
            admin_user=admin_user,
            action="prompt_rule_created",
            resource_type="prompt_rule",
            resource_id=None,
            before_state=None,
            after_state={"rules_seeded": list(BASE_RULES.keys())},
            description="Seeded 17 base rules (A-Q)",
        )
        db.commit()
        for rule in rules:
            db.refresh(rule)
        return rules

    # ------------------------------------------------------------------
    # 15. Preview prompt built from DB rules
    # ------------------------------------------------------------------
    @staticmethod
    def preview_prompt(
        db: Session, niche: str, language: str
    ) -> dict:
        """Build prompt using active DB rules. Falls back to hardcoded prompt."""
        try:
            from app.llm.prompts.hook_identification import build_hook_prompt_from_rules

            rules = AdminService.get_active_rules_as_dicts(db)
            prompt_text = build_hook_prompt_from_rules(
                rules=rules,
                niche=niche,
                transcript="[PREVIEW \u2014 no transcript]",
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

    # ------------------------------------------------------------------
    # 16. Rule history
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 17. List provider configs
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 18. Update provider
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 19. Set primary provider
    # ------------------------------------------------------------------
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

        # Unset all is_primary
        db.execute(
            update(ProviderConfig).values(is_primary=False)
        )

        target.is_primary = True
        target.is_enabled = True
        target.updated_by = admin_user.id

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

    # ------------------------------------------------------------------
    # 20. Set API key
    # ------------------------------------------------------------------
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
            raise ValueError("API key contains invalid characters")

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
            env_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                ".env",
            )
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

                    with open(env_path, "w") as f:
                        f.writelines(new_lines)
                else:
                    with open(env_path, "w") as f:
                        f.write(f"{env_var}={api_key}\n")
            except OSError as e:
                logger.error("Failed to write API key to .env: %s", e)

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

    # ------------------------------------------------------------------
    # 21. Trigger NARM analysis
    # ------------------------------------------------------------------
    @staticmethod
    def trigger_narm_analysis(
        db: Session, time_range_days: int, admin_user: User
    ) -> list[NarmInsight]:
        """
        Query LearningLog aggregates, call primary LLM provider to
        generate insights, store and return NarmInsight records.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=time_range_days)

        try:
            # --- Hook selection rates by hook_type ---
            presented_stmt = (
                select(
                    LearningLog.event_metadata["hook_type"].label("hook_type"),
                    func.count(LearningLog.id).label("cnt"),
                )
                .where(
                    LearningLog.event_type == "hook_presented",
                    LearningLog.created_at >= cutoff,
                )
                .group_by("hook_type")
            )
            selected_stmt = (
                select(
                    LearningLog.event_metadata["hook_type"].label("hook_type"),
                    func.count(LearningLog.id).label("cnt"),
                )
                .where(
                    LearningLog.event_type == "hook_selected",
                    LearningLog.created_at >= cutoff,
                )
                .group_by("hook_type")
            )

            presented_rows = db.execute(presented_stmt).all()
            selected_rows = db.execute(selected_stmt).all()

            presented_map = {
                str(row.hook_type): row.cnt for row in presented_rows
            }
            selected_map = {
                str(row.hook_type): row.cnt for row in selected_rows
            }

            selection_rates = {}
            for ht, presented_count in presented_map.items():
                sel_count = selected_map.get(ht, 0)
                rate = (sel_count / presented_count * 100) if presented_count > 0 else 0
                selection_rates[ht] = {
                    "presented": presented_count,
                    "selected": sel_count,
                    "rate_pct": round(rate, 1),
                }

            # --- Most popular niches ---
            niche_stmt = (
                select(
                    LearningLog.niche,
                    func.count(LearningLog.id).label("cnt"),
                )
                .where(
                    LearningLog.event_type == "hook_presented",
                    LearningLog.created_at >= cutoff,
                )
                .group_by(LearningLog.niche)
                .order_by(desc("cnt"))
                .limit(10)
            )
            niche_rows = db.execute(niche_stmt).all()
            popular_niches = [
                {"niche": row.niche, "count": row.cnt}
                for row in niche_rows
            ]

            # --- Regeneration rate ---
            total_sessions_count = db.scalar(
                select(func.count(func.distinct(LearningLog.session_id)))
                .where(LearningLog.created_at >= cutoff)
            ) or 0

            regen_sessions_count = db.scalar(
                select(func.count(func.distinct(LearningLog.session_id)))
                .where(
                    LearningLog.event_type == "regeneration_triggered",
                    LearningLog.created_at >= cutoff,
                )
            ) or 0

            regen_rate = (
                (regen_sessions_count / total_sessions_count * 100)
                if total_sessions_count > 0
                else 0
            )

            # --- Average attention scores by niche ---
            attn_stmt = (
                select(
                    AnalysisSession.niche,
                    func.avg(Hook.attention_score).label("avg_score"),
                )
                .join(
                    AnalysisSession,
                    Hook.session_id == AnalysisSession.id,
                )
                .where(AnalysisSession.created_at >= cutoff)
                .group_by(AnalysisSession.niche)
            )
            attn_rows = db.execute(attn_stmt).all()
            avg_attention = {
                row.niche: round(float(row.avg_score), 2)
                for row in attn_rows
                if row.avg_score is not None
            }

            # --- Build summary ---
            summary = {
                "time_range_days": time_range_days,
                "hook_selection_rates": selection_rates,
                "popular_niches": popular_niches,
                "regeneration_rate_pct": round(regen_rate, 1),
                "total_sessions": total_sessions_count,
                "regen_sessions": regen_sessions_count,
                "avg_attention_by_niche": avg_attention,
            }

            # --- Call LLM ---
            llm_prompt = (
                "You are an analytics expert for HookCut, a YouTube Shorts "
                "hook extraction platform. Analyze this data and generate "
                "3-5 actionable insights.\n\n"
                f"DATA:\n{json.dumps(summary, indent=2)}\n\n"
                "Return ONLY valid JSON array with 3-5 objects, each with:\n"
                '{"insight_type": "hook_preference|niche_trend|'
                'regeneration_pattern|engagement_pattern",\n'
                ' "title": "short title",\n'
                ' "content": "detailed insight (2-3 sentences)",\n'
                ' "confidence": "high|medium|low"}\n'
            )

            insights: list[NarmInsight] = []

            try:
                from app.llm.provider import get_provider
                from app.config import get_settings

                provider = get_provider(
                    get_settings().LLM_PRIMARY_PROVIDER
                )
                response = provider.generate(llm_prompt, max_tokens=2000)
                raw_text = response.text.strip()

                # Try to parse JSON from the response
                # Handle markdown code blocks wrapping
                if raw_text.startswith("```"):
                    raw_text = re.sub(
                        r"^```(?:json)?\s*", "", raw_text
                    )
                    raw_text = re.sub(r"\s*```$", "", raw_text)

                parsed = json.loads(raw_text)
                if not isinstance(parsed, list):
                    parsed = [parsed]

                for item in parsed[:5]:
                    insight = NarmInsight(
                        insight_type=item.get(
                            "insight_type", "engagement_pattern"
                        ),
                        title=item.get("title", "Untitled Insight"),
                        content=item.get("content", ""),
                        data_summary=summary,
                        confidence=item.get("confidence", "medium"),
                        time_range_days=time_range_days,
                    )
                    db.add(insight)
                    insights.append(insight)

            except Exception as llm_err:
                logger.warning(
                    "LLM call for NARM failed, generating basic insights: %s",
                    llm_err,
                )
                # Generate basic insights from data without LLM
                basic_insight = NarmInsight(
                    insight_type="engagement_pattern",
                    title=f"Data summary for last {time_range_days} days",
                    content=(
                        f"Analyzed {total_sessions_count} sessions. "
                        f"Regeneration rate: {round(regen_rate, 1)}%. "
                        f"Top niches: {', '.join(n['niche'] for n in popular_niches[:3])}."
                    ),
                    data_summary=summary,
                    confidence="low",
                    time_range_days=time_range_days,
                )
                db.add(basic_insight)
                insights.append(basic_insight)

            db.flush()

            AdminService.create_audit_log(
                db,
                admin_user=admin_user,
                action="narm_triggered",
                resource_type="narm_insight",
                resource_id=None,
                before_state=None,
                after_state={
                    "time_range_days": time_range_days,
                    "insights_generated": len(insights),
                },
                description=(
                    f"Triggered NARM analysis for {time_range_days} days, "
                    f"generated {len(insights)} insights"
                ),
            )
            db.commit()
            for ins in insights:
                db.refresh(ins)
            return insights

        except HookCutError:
            raise
        except Exception as e:
            db.rollback()
            logger.exception("NARM analysis failed")
            raise HookCutError(f"NARM analysis error: {e}") from e

    # ------------------------------------------------------------------
    # 22. Get latest NARM insights
    # ------------------------------------------------------------------
    @staticmethod
    def get_narm_insights(db: Session) -> list[NarmInsight]:
        """Latest insights ordered by created_at desc, limit 20."""
        stmt = (
            select(NarmInsight)
            .order_by(desc(NarmInsight.created_at))
            .limit(20)
        )
        return list(db.scalars(stmt).all())
