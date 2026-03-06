import logging
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from app.tasks.celery_app import celery_app
from app.dependencies import get_db_session
from app.services.credit_manager import CreditManager

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=0)
def run_analysis(self, session_id: str):
    """
    Main analysis task: transcript fetch → LLM hook identification.
    Retry: handled internally (3 LLM attempts with backoff).
    On total failure: credits refunded automatically.
    """
    db = get_db_session()
    try:
        from app.models.session import AnalysisSession, Hook
        from app.models.learning import LearningLog
        from app.services.transcript import TranscriptService
        from app.services.hook_engine import HookEngine
        from app.exceptions import HookEngineError

        session = db.get(AnalysisSession, session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return {"error": "Session not found"}

        # --- Step 1: Fetch transcript ---
        session.status = "fetching_transcript"
        db.commit()
        self.update_state(state="PROGRESS", meta={"stage": "Fetching transcript...", "progress": 10})

        transcript_service = TranscriptService()
        transcript_result = transcript_service.fetch(session.video_id, session.language)

        if not transcript_result:
            # All 3 providers failed — refund credits
            CreditManager(db).refund_and_fail(
                session_id,
                error_msg="No transcript found. Try a video with captions enabled.",
                _logger=logger,
            )
            return {"error": "Transcript unavailable"}

        # --- Step 2: LLM hook identification ---
        session.transcript_provider = transcript_result.provider
        session.transcript_text = transcript_result.text
        session.status = "analyzing"
        db.commit()
        self.update_state(state="PROGRESS", meta={"stage": "Analyzing hooks...", "progress": 40})

        hook_engine = HookEngine()
        try:
            result = hook_engine.analyze(
                transcript=transcript_result.text,
                niche=session.niche,
                language=session.language,
            )
        except HookEngineError as e:
            CreditManager(db).refund_and_fail(
                session_id,
                error_msg="Analysis unavailable. Credits not deducted. Try again.",
                _logger=logger,
            )
            return {"error": str(e)}

        # --- Step 3: Store hooks ---
        self.update_state(state="PROGRESS", meta={"stage": "Saving hooks...", "progress": 80})

        try:
            # Clear any previous hooks (from regeneration)
            db.execute(delete(Hook).where(Hook.session_id == session_id))

            for candidate in result.hooks:
                hook = Hook(
                    session_id=session_id,
                    rank=candidate.rank,
                    hook_text=candidate.hook_text,
                    start_time=candidate.start_time,
                    end_time=candidate.end_time,
                    start_seconds=candidate.start_seconds,
                    end_seconds=candidate.end_seconds,
                    hook_type=candidate.hook_type,
                    funnel_role=candidate.funnel_role,
                    scores=candidate.scores,
                    attention_score=candidate.attention_score,
                    platform_dynamics=candidate.platform_dynamics,
                    viewer_psychology=candidate.viewer_psychology,
                    improvement_suggestion=candidate.improvement_suggestion,
                    is_composite=candidate.is_composite,
                )
                db.add(hook)

            db.flush()
        except SQLAlchemyError as e:
            logger.exception(f"Failed to save hooks for session {session_id}: {e}")
            db.rollback()
            CreditManager(db).refund_and_fail(
                session_id,
                error_msg="Analysis complete but failed to save results. Credits not deducted. Please try again.",
                _logger=logger,
            )
            return {"error": "Failed to save hooks"}

        # Log learning events: hook_presented
        hooks = db.execute(
            select(Hook).where(Hook.session_id == session_id)
        ).scalars().all()
        for hook in hooks:
            log_entry = LearningLog(
                session_id=session_id,
                event_type="hook_presented",
                hook_id=hook.id,
                video_id=session.video_id,
                niche=session.niche,
                language=session.language,
                event_metadata={
                    "hook_type": hook.hook_type,
                    "attention_score": hook.attention_score,
                    "start_time": hook.start_time,
                    "end_time": hook.end_time,
                    "rank": hook.rank,
                },
            )
            db.add(log_entry)

        session.status = "hooks_ready"
        db.commit()

        self.update_state(state="PROGRESS", meta={"stage": "Hooks ready!", "progress": 100})

        return {
            "session_id": session_id,
            "hooks_count": len(result.hooks),
            "provider": result.provider,
            "attempts": result.attempts,
        }

    except Exception as e:
        logger.exception(f"Analysis task failed for session {session_id}: {e}")
        user_msg = _friendly_error(e)
        try:
            CreditManager(db).refund_and_fail(
                session_id,
                error_msg=user_msg,
                _logger=logger,
            )
        except Exception as inner_err:
            logger.exception(f"Failed to refund/fail session {session_id}: {inner_err}")
        return {"error": user_msg}
    finally:
        db.close()


def _friendly_error(exc: Exception) -> str:
    """Convert a raw exception into a short, user-facing message."""
    s = str(exc).lower()
    if "transcript" in s or "caption" in s:
        return "No transcript found. Try a video with captions enabled."
    if "rate limit" in s or "429" in s:
        return "AI service is busy. Please wait a moment and try again."
    if "timeout" in s or "timed out" in s:
        return "Analysis timed out. Please try again."
    if "api key" in s or "authentication" in s or "401" in s or "403" in s:
        return "AI service configuration error. Please contact support."
    if any(db_kw in s for db_kw in ("sqlalchemy", "psycopg", "sqlite", "truncat", "column", "data too long")):
        return "Analysis complete but failed to save results. Credits not deducted. Please try again."
    return "Analysis failed. Please try again."
