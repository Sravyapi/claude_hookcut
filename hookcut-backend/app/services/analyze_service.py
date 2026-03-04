"""
AnalyzeService — owns all analysis business logic.

Routers call these static methods and convert HookCutError to HTTPException.
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import (
    InvalidURLError,
    MetadataFetchError,
    VideoAccessibilityError,
    InsufficientCreditsError,
    SessionNotFoundError,
    InvalidStateError,
    HooksNotReadyError,
)
from app.llm.prompts.constants import get_regen_fee
from app.models.billing import Transaction
from app.models.learning import LearningLog
from app.models.session import AnalysisSession, Hook, Short
from app.models.user import User, CreditBalance
from app.schemas.analysis import (
    VideoValidateRequest,
    VideoValidateResponse,
)
from app.services.analytics import track
from app.services.credit_manager import CreditManager
from app.services.video_metadata import VideoMetadataService
from app.tasks.analyze_task import run_analysis
from app.tasks.generate_short_task import generate_short
from app.utils.youtube import validate_youtube_url

logger = logging.getLogger(__name__)


class AnalyzeService:

    @staticmethod
    def validate_url(req: VideoValidateRequest) -> VideoValidateResponse:
        """Validate YouTube URL and return video metadata."""
        valid, video_id, error = validate_youtube_url(req.youtube_url)
        if not valid:
            return VideoValidateResponse(valid=False, error=error)

        metadata_svc = VideoMetadataService()
        metadata = metadata_svc.fetch(video_id)
        if not metadata:
            return VideoValidateResponse(valid=False, error="Could not fetch video metadata")

        ok, err = metadata_svc.validate_accessibility(metadata)
        if not ok:
            return VideoValidateResponse(valid=False, error=err)

        return VideoValidateResponse(
            valid=True,
            video_id=video_id,
            title=metadata.title,
            duration_seconds=metadata.duration_seconds,
        )

    @staticmethod
    def start_analysis(
        db: Session,
        user_id: str,
        youtube_url: str,
        niche: str,
        language: str,
    ) -> dict:
        """
        Full analysis pipeline: validate URL, fetch metadata, check credits,
        create session, deduct credits, dispatch Celery task, track analytics.

        Returns dict with session_id, task_id, video_title, video_duration_seconds,
        minutes_charged, is_watermarked.

        Raises: InvalidURLError, MetadataFetchError, VideoAccessibilityError,
                InsufficientCreditsError
        """
        AnalyzeService._ensure_user(db, user_id)

        # Validate URL
        valid, video_id, error = validate_youtube_url(youtube_url)
        if not valid:
            raise InvalidURLError(error)

        # Fetch metadata
        metadata_svc = VideoMetadataService()
        metadata = metadata_svc.fetch(video_id)
        if not metadata:
            raise MetadataFetchError()

        ok, err = metadata_svc.validate_accessibility(metadata)
        if not ok:
            raise VideoAccessibilityError(err)

        # Calculate minutes needed (source video duration)
        minutes_needed = metadata.duration_seconds / 60.0

        # Check balance
        credit_mgr = CreditManager(db)
        has_enough, available = credit_mgr.check_balance(user_id, minutes_needed)
        if not has_enough:
            raise InsufficientCreditsError(
                f"Insufficient minutes. Available: {available:.1f}, needed: {minutes_needed:.1f}. "
                "Please top up your account."
            )

        # Create session first so we have a real session_id for the transaction
        session = AnalysisSession(
            user_id=user_id,
            youtube_url=youtube_url,
            video_id=video_id,
            video_title=metadata.title,
            video_duration_seconds=metadata.duration_seconds,
            niche=niche,
            language=language,
            status="pending",
            minutes_charged=minutes_needed,
        )
        db.add(session)
        db.flush()

        # Deduct credits with real session_id
        deduction = credit_mgr.deduct(user_id, minutes_needed, session_id=session.id)
        if not deduction.success:
            db.rollback()
            raise InsufficientCreditsError(deduction.error)

        session.credits_source = deduction.credits_source
        session.is_watermarked = deduction.is_watermarked
        session.paid_minutes_used = deduction.paid_used
        session.payg_minutes_used = deduction.payg_used
        session.free_minutes_used = deduction.free_used
        db.commit()
        db.refresh(session)

        # Dispatch Celery task
        task = run_analysis.delay(session.id)
        session.task_id = task.id
        db.commit()

        track(user_id, "analysis_started", {
            "session_id": session.id,
            "video_id": video_id,
            "niche": niche,
            "minutes_charged": minutes_needed,
        })

        return {
            "session_id": session.id,
            "task_id": task.id,
            "video_title": metadata.title,
            "video_duration_seconds": metadata.duration_seconds,
            "minutes_charged": minutes_needed,
            "is_watermarked": deduction.is_watermarked,
        }

    @staticmethod
    def get_hooks(db: Session, session_id: str) -> dict:
        """
        Get hooks for a session.

        Returns dict for HooksListResponse.
        Raises: SessionNotFoundError
        """
        session = db.get(AnalysisSession, session_id)
        if not session:
            raise SessionNotFoundError()

        hooks = (
            db.execute(
                select(Hook)
                .where(Hook.session_id == session_id)
                .order_by(Hook.rank)
            ).scalars().all()
        )

        return {
            "session": session,
            "hooks": hooks,
        }

    @staticmethod
    def regenerate_hooks(db: Session, session_id: str) -> dict:
        """
        Regenerate hooks. 1st free, 2nd+ charged.

        Returns dict for RegenerateResponse.
        Raises: SessionNotFoundError, InvalidStateError
        """
        session = db.get(AnalysisSession, session_id)
        if not session:
            raise SessionNotFoundError()

        if session.status not in ("hooks_ready", "completed"):
            raise InvalidStateError("Session is not in a state that allows regeneration")

        session.regeneration_count += 1
        fee_charged = None
        currency = None

        # 2nd+ regeneration: charge fee
        if session.regeneration_count >= 2:
            user = db.get(User, session.user_id)
            currency = user.currency if user else "USD"
            fee = get_regen_fee(session.video_duration_seconds, currency)

            txn = Transaction(
                user_id=session.user_id,
                type="regeneration_fee",
                session_id=session.id,
                money_amount=fee,
                currency=currency,
                description=f"Regeneration #{session.regeneration_count} fee",
            )
            db.add(txn)
            fee_charged = fee

        # Log learning event
        previous_hooks = db.execute(
            select(Hook).where(Hook.session_id == session_id)
        ).scalars().all()
        log_entry = LearningLog(
            session_id=session_id,
            event_type="regeneration_triggered",
            video_id=session.video_id,
            niche=session.niche,
            language=session.language,
            event_metadata={
                "regeneration_count": session.regeneration_count,
                "previous_hook_ids": [h.id for h in previous_hooks],
            },
        )
        db.add(log_entry)

        session.status = "pending"
        db.commit()

        # Dispatch new analysis task
        task = run_analysis.delay(session.id)
        session.task_id = task.id
        db.commit()

        return {
            "session_id": session.id,
            "task_id": task.id,
            "regeneration_count": session.regeneration_count,
            "fee_charged": fee_charged,
            "currency": currency,
        }

    @staticmethod
    def select_hooks(
        db: Session,
        session_id: str,
        hook_ids: list[str],
        caption_style: str,
        time_overrides: dict,
    ) -> dict:
        """
        Select hooks and dispatch Short generation tasks.

        Returns dict for SelectHooksResponse.
        Raises: SessionNotFoundError, HooksNotReadyError, InvalidStateError
        """
        session = db.get(AnalysisSession, session_id)
        if not session:
            raise SessionNotFoundError()

        if session.status != "hooks_ready":
            raise HooksNotReadyError()

        # Validate hook IDs belong to this session
        hooks = db.execute(
            select(Hook).where(Hook.session_id == session_id)
        ).scalars().all()
        hook_map = {h.id: h for h in hooks}

        for hook_id in hook_ids:
            if hook_id not in hook_map:
                raise InvalidStateError(f"Hook {hook_id} not found in this session")

        # Validate time overrides
        for hook_id, override in time_overrides.items():
            if hook_id not in hook_map:
                raise InvalidStateError(f"Time override for unknown hook {hook_id}")
            orig = hook_map[hook_id]
            if override.end_seconds <= override.start_seconds + 5:
                raise InvalidStateError("Trimmed hook must be at least 5 seconds")
            if override.start_seconds < max(0, orig.start_seconds - 10):
                raise InvalidStateError("Start time cannot be more than 10s before original")
            if override.end_seconds > orig.end_seconds + 10:
                raise InvalidStateError("End time cannot be more than 10s after original")

        # Mark selected/not-selected and log events
        for hook in hooks:
            if hook.id in hook_ids:
                hook.is_selected = True
                db.add(LearningLog(
                    session_id=session_id,
                    event_type="hook_selected",
                    hook_id=hook.id,
                    video_id=session.video_id,
                    niche=session.niche,
                    language=session.language,
                    event_metadata={
                        "selection_order": hook_ids.index(hook.id) + 1,
                        "hook_type": hook.hook_type,
                    },
                ))
            else:
                db.add(LearningLog(
                    session_id=session_id,
                    event_type="hook_not_selected",
                    hook_id=hook.id,
                    video_id=session.video_id,
                    niche=session.niche,
                    language=session.language,
                    event_metadata={"hook_type": hook.hook_type},
                ))

        # Create Short records and dispatch tasks
        short_ids = []
        task_ids = []

        for hook_id in hook_ids:
            override = time_overrides.get(hook_id)
            short = Short(
                session_id=session_id,
                hook_id=hook_id,
                status="queued",
                caption_style=caption_style,
                start_seconds_override=override.start_seconds if override else None,
                end_seconds_override=override.end_seconds if override else None,
                is_watermarked=session.is_watermarked,
            )
            db.add(short)
            db.flush()

            task = generate_short.delay(short.id)
            short.task_id = task.id
            short_ids.append(short.id)
            task_ids.append(task.id)

        session.status = "generating_shorts"
        db.commit()

        return {
            "short_ids": short_ids,
            "task_ids": task_ids,
        }

    @staticmethod
    def _ensure_user(db: Session, user_id: str) -> None:
        """Auto-create user if not exists."""
        user = db.get(User, user_id)
        if not user:
            user = User(id=user_id, email=f"{user_id}@hookcut.local", currency="USD")
            db.add(user)
            db.flush()
        balance = db.execute(
            select(CreditBalance).where(CreditBalance.user_id == user_id)
        ).scalar_one_or_none()
        if not balance:
            balance = CreditBalance(user_id=user_id)
            db.add(balance)
        db.commit()
