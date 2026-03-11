"""
AdminService — core admin business logic (dashboard, users, sessions, audit).

Rule CRUD, provider management, and NARM analytics have been extracted to:
- admin_rule_service.py (AdminRuleService)
- admin_provider_service.py (AdminProviderService)
- narm_service.py (NarmService)

This module re-exports those classes for backwards compatibility.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from app.models.user import User, Subscription
from app.models.session import AnalysisSession, Short
from app.models.admin import AdminAuditLog
from app.exceptions import ResourceNotFoundError, HookCutError

logger = logging.getLogger(__name__)


def _escape_sql_like(value: str) -> str:
    """Escape SQL LIKE wildcards to prevent unintended pattern matching."""
    return value.replace("%", "\\%").replace("_", "\\_")


class AdminService:
    """All methods are static — no instance state required."""

    # ------------------------------------------------------------------
    # 1. Dashboard stats
    # ------------------------------------------------------------------
    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        """Aggregate counts and last 10 sessions with user email."""
        try:
            # Single query with scalar subqueries — 1 round-trip instead of 4
            counts = db.execute(
                select(
                    select(func.count(User.id)).scalar_subquery().label("users"),
                    select(func.count(AnalysisSession.id)).scalar_subquery().label("sessions"),
                    select(func.count(Short.id)).scalar_subquery().label("shorts"),
                    select(func.count(Subscription.id)).where(
                        Subscription.status == "active"
                    ).scalar_subquery().label("active_subs"),
                )
            ).one()
            total_users = counts.users or 0
            total_sessions = counts.sessions or 0
            total_shorts = counts.shorts or 0
            active_subs = counts.active_subs or 0

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
        db: Session, page: int = 1, per_page: int = 20, search: str | None = None
    ) -> dict:
        """Return paginated users with per-user session counts. Optional email search."""
        try:
            count_stmt = select(func.count(User.id))

            if search:
                safe_search = _escape_sql_like(search)
                search_filter = User.email.ilike(f"%{safe_search}%")
                count_stmt = count_stmt.where(search_filter)

            total = db.scalar(count_stmt) or 0

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
            )

            if search:
                safe_search = _escape_sql_like(search)
                stmt = stmt.where(User.email.ilike(f"%{safe_search}%"))

            stmt = (
                stmt.order_by(desc(User.created_at))
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
        from sqlalchemy.orm import selectinload
        row = db.execute(
            select(AnalysisSession, User.email)
            .join(User, AnalysisSession.user_id == User.id)
            .where(AnalysisSession.id == session_id)
            .options(selectinload(AnalysisSession.hooks), selectinload(AnalysisSession.shorts))
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

        # Truncate transcript to avoid returning 100KB+ payloads in admin detail
        transcript_preview: str | None = None
        if session.transcript_text:
            transcript_preview = (
                session.transcript_text[:500] + "..."
                if len(session.transcript_text) > 500
                else session.transcript_text
            )

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
            "transcript": transcript_preview,
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

            # Cap at 10,000 to prevent OOM on large date ranges.
            stmt = stmt.order_by(desc(AdminAuditLog.created_at)).limit(10_000)
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


# Re-exports for backwards compatibility
from app.services.admin_rule_service import AdminRuleService  # noqa: F401, E402
from app.services.admin_provider_service import AdminProviderService  # noqa: F401, E402
from app.services.narm_service import NarmService  # noqa: F401, E402

# Proxy methods on AdminService for backwards compatibility with existing callers
# (tests and other code that call AdminService.list_rules, etc.)
AdminService.list_rules = staticmethod(AdminRuleService.list_rules)  # type: ignore[attr-defined]
AdminService.get_active_rules_as_dicts = staticmethod(AdminRuleService.get_active_rules_as_dicts)  # type: ignore[attr-defined]
AdminService.create_rule = staticmethod(AdminRuleService.create_rule)  # type: ignore[attr-defined]
AdminService.update_rule = staticmethod(AdminRuleService.update_rule)  # type: ignore[attr-defined]
AdminService.revert_rule = staticmethod(AdminRuleService.revert_rule)  # type: ignore[attr-defined]
AdminService.delete_rule = staticmethod(AdminRuleService.delete_rule)  # type: ignore[attr-defined]
AdminService.seed_rules = staticmethod(AdminRuleService.seed_rules)  # type: ignore[attr-defined]
AdminService.preview_prompt = staticmethod(AdminRuleService.preview_prompt)  # type: ignore[attr-defined]
AdminService.get_rule_history = staticmethod(AdminRuleService.get_rule_history)  # type: ignore[attr-defined]
AdminService.list_providers = staticmethod(AdminProviderService.list_providers)  # type: ignore[attr-defined]
AdminService.update_provider = staticmethod(AdminProviderService.update_provider)  # type: ignore[attr-defined]
AdminService.set_primary_provider = staticmethod(AdminProviderService.set_primary_provider)  # type: ignore[attr-defined]
AdminService.set_api_key = staticmethod(AdminProviderService.set_api_key)  # type: ignore[attr-defined]
AdminService.trigger_narm_analysis = staticmethod(NarmService.trigger_narm_analysis)  # type: ignore[attr-defined]
AdminService.get_narm_insights = staticmethod(NarmService.get_narm_insights)  # type: ignore[attr-defined]
AdminService._aggregate_hook_selection_data = staticmethod(NarmService._aggregate_hook_selection_data)  # type: ignore[attr-defined]
AdminService._aggregate_niche_data = staticmethod(NarmService._aggregate_niche_data)  # type: ignore[attr-defined]
AdminService._aggregate_attention_scores = staticmethod(NarmService._aggregate_attention_scores)  # type: ignore[attr-defined]
AdminService._build_narm_summary = staticmethod(NarmService._build_narm_summary)  # type: ignore[attr-defined]
