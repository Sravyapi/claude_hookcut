"""
UserService — owns all user profile, balance, and history business logic.

Routers call these static methods and convert HookCutError to HTTPException.
"""
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import UserNotFoundError, InvalidStateError
from app.models.session import AnalysisSession
from app.models.user import User
from app.schemas.billing import BalanceResponse
from app.services.credit_manager import CreditManager

logger = logging.getLogger(__name__)


class UserService:

    @staticmethod
    def get_balance(db: Session, user_id: str) -> BalanceResponse:
        """Get current credit balance for the authenticated user."""
        credit_mgr = CreditManager(db)
        balance = credit_mgr.get_balance(user_id)

        return BalanceResponse(
            paid_minutes_remaining=balance.paid_minutes_remaining,
            paid_minutes_total=balance.paid_minutes_total,
            free_minutes_remaining=balance.free_minutes_remaining,
            free_minutes_total=balance.free_minutes_total,
            payg_minutes_remaining=balance.payg_minutes_remaining,
            total_available=balance.total_available,
        )

    @staticmethod
    def get_history(db: Session, user_id: str, page: int, per_page: int) -> dict:
        """
        Get past analysis sessions for the authenticated user.

        Returns dict with sessions list, total, page, per_page.
        """
        offset = (max(page, 1) - 1) * per_page
        total = db.execute(
            select(func.count()).select_from(AnalysisSession)
            .where(AnalysisSession.user_id == user_id)
        ).scalar()
        sessions = db.execute(
            select(AnalysisSession)
            .where(AnalysisSession.user_id == user_id)
            .order_by(AnalysisSession.created_at.desc())
            .offset(offset)
            .limit(per_page)
        ).scalars().all()

        return {
            "sessions": [
                {
                    "id": s.id,
                    "video_title": s.video_title,
                    "video_id": s.video_id,
                    "niche": s.niche,
                    "language": s.language,
                    "status": s.status,
                    "minutes_charged": s.minutes_charged,
                    "is_watermarked": s.is_watermarked,
                    "regeneration_count": s.regeneration_count,
                    "created_at": s.created_at.isoformat(),
                }
                for s in sessions
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def get_profile(db: Session, user_id: str) -> dict:
        """
        Get user profile.

        Raises: UserNotFoundError
        """
        user = db.get(User, user_id)
        if not user:
            raise UserNotFoundError()

        return {
            "id": user.id,
            "email": user.email,
            "currency": user.currency,
            "plan_tier": user.plan_tier,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        }

    @staticmethod
    def update_currency(db: Session, user_id: str, currency: str) -> dict:
        """
        Change preferred currency.

        Raises: InvalidStateError (bad currency), UserNotFoundError
        """
        if currency not in ("INR", "USD"):
            raise InvalidStateError("Currency must be INR or USD")

        user = db.get(User, user_id)
        if not user:
            raise UserNotFoundError()

        user.currency = currency
        db.commit()
        return {"currency": currency}
