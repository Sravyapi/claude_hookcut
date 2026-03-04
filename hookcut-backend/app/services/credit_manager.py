import logging
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import CreditBalance
from app.models.billing import Transaction
from app.models.session import AnalysisSession

logger = logging.getLogger(__name__)


@dataclass
class DeductionResult:
    success: bool
    paid_used: float
    payg_used: float
    free_used: float
    is_watermarked: bool
    error: Optional[str] = None

    @property
    def total_used(self) -> float:
        return self.paid_used + self.payg_used + self.free_used

    @property
    def credits_source(self) -> str:
        sources = []
        if self.paid_used > 0:
            sources.append("paid")
        if self.payg_used > 0:
            sources.append("payg")
        if self.free_used > 0:
            sources.append("free")
        if len(sources) > 1:
            return "mixed"
        return sources[0] if sources else "free"


class CreditManager:
    def __init__(self, db: Session):
        self.db = db

    def check_balance(self, user_id: str, minutes_needed: float) -> tuple[bool, float]:
        """Check if user has sufficient minutes. Returns (has_enough, total_available)."""
        balance = self._get_or_create_balance(user_id)
        return balance.total_available >= minutes_needed, balance.total_available

    def deduct(
        self, user_id: str, minutes: float, session_id: str
    ) -> DeductionResult:
        """
        Deduct minutes in order: paid → PAYG → free.
        If ANY free minutes used, session is watermarked.
        Uses a savepoint to prevent race conditions between balance check and deduction.
        """
        balance = self._get_or_create_balance(user_id)

        if balance.total_available < minutes:
            return DeductionResult(
                success=False, paid_used=0, payg_used=0, free_used=0,
                is_watermarked=False,
                error=f"Insufficient minutes. Available: {balance.total_available:.1f}, "
                      f"needed: {minutes:.1f}",
            )

        with self.db.begin_nested():
            remaining = minutes
            paid_used = 0.0
            payg_used = 0.0
            free_used = 0.0

            # 1. Paid minutes first
            if remaining > 0 and balance.paid_minutes_remaining > 0:
                take = min(remaining, balance.paid_minutes_remaining)
                balance.paid_minutes_remaining -= take
                paid_used = take
                remaining -= take

            # 2. PAYG minutes second
            if remaining > 0 and balance.payg_minutes_remaining > 0:
                take = min(remaining, balance.payg_minutes_remaining)
                balance.payg_minutes_remaining -= take
                payg_used = take
                remaining -= take

            # 3. Free minutes last (triggers watermark)
            if remaining > 0 and balance.free_minutes_remaining > 0:
                take = min(remaining, balance.free_minutes_remaining)
                balance.free_minutes_remaining -= take
                free_used = take
                remaining -= take

            is_watermarked = free_used > 0

            # Log transaction
            result = DeductionResult(
                success=True, paid_used=paid_used, payg_used=payg_used,
                free_used=free_used, is_watermarked=is_watermarked,
            )

            transaction = Transaction(
                user_id=user_id,
                type="credit_deduction",
                session_id=session_id,
                minutes_amount=minutes,
                description=(
                    f"Deducted {minutes:.1f} min "
                    f"(paid={paid_used:.1f}, payg={payg_used:.1f}, free={free_used:.1f})"
                ),
            )
            self.db.add(transaction)

        self.db.commit()

        return result

    def refund(
        self, user_id: str, session_id: str,
        paid_minutes: float = 0, payg_minutes: float = 0, free_minutes: float = 0,
    ):
        """Refund credits to the SAME buckets they were deducted from."""
        balance = self._get_or_create_balance(user_id)

        balance.paid_minutes_remaining += paid_minutes
        balance.payg_minutes_remaining += payg_minutes
        balance.free_minutes_remaining += free_minutes

        total = paid_minutes + payg_minutes + free_minutes
        transaction = Transaction(
            user_id=user_id,
            type="credit_refund",
            session_id=session_id,
            minutes_amount=total,
            description=(
                f"Refunded {total:.1f} min "
                f"(paid={paid_minutes:.1f}, payg={payg_minutes:.1f}, free={free_minutes:.1f})"
            ),
        )
        self.db.add(transaction)
        self.db.commit()
        logger.info(f"Refunded {total:.1f} min to user {user_id} for session {session_id}")

    def add_paid_minutes(self, user_id: str, minutes: float, provider: str, provider_ref: str):
        """Add paid subscription minutes (on billing cycle start)."""
        balance = self._get_or_create_balance(user_id)
        balance.paid_minutes_remaining = minutes   # reset to new billing cycle allocation
        balance.paid_minutes_total = minutes

        transaction = Transaction(
            user_id=user_id,
            type="subscription_payment",
            minutes_amount=minutes,
            provider=provider,
            provider_ref=provider_ref,
            description=f"Subscription: {minutes:.0f} min provisioned",
        )
        self.db.add(transaction)
        self.db.commit()

    def add_payg_minutes(
        self, user_id: str, minutes: float,
        amount: int, currency: str, provider: str, provider_ref: str,
    ):
        """Add PAYG minutes (no expiry)."""
        balance = self._get_or_create_balance(user_id)
        balance.payg_minutes_remaining += minutes

        transaction = Transaction(
            user_id=user_id,
            type="payg_purchase",
            minutes_amount=minutes,
            money_amount=amount,
            currency=currency,
            provider=provider,
            provider_ref=provider_ref,
            description=f"PAYG: {minutes:.0f} min purchased",
        )
        self.db.add(transaction)
        self.db.commit()

    def refund_and_fail(
        self, session_id: str, error_msg: str, _logger=None
    ) -> None:
        """Refund credits for a failed session and mark it as failed."""
        _log = _logger or logger
        session = self.db.get(AnalysisSession, session_id)
        if not session:
            _log.error(f"refund_and_fail: session {session_id} not found")
            return

        if not session.credits_refunded and session.minutes_charged > 0:
            self.refund(
                user_id=session.user_id,
                session_id=session.id,
                paid_minutes=session.paid_minutes_used,
                payg_minutes=session.payg_minutes_used,
                free_minutes=session.free_minutes_used,
            )
            session.credits_refunded = True

        session.status = "failed"
        session.error_message = error_msg
        self.db.commit()
        _log.info(f"Session {session_id} failed and credits refunded: {error_msg}")

    def get_balance(self, user_id: str) -> CreditBalance:
        return self._get_or_create_balance(user_id)

    def _get_or_create_balance(self, user_id: str) -> CreditBalance:
        balance = self.db.execute(select(CreditBalance).where(CreditBalance.user_id == user_id)).scalar_one_or_none()
        if not balance:
            balance = CreditBalance(user_id=user_id)
            self.db.add(balance)
            self.db.commit()
            self.db.refresh(balance)
        return balance
