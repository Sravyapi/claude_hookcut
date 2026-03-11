"""ClipService — manual clip generation business logic."""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.exceptions import (
    InvalidStateError,
    InvalidURLError,
    SessionNotFoundError,
    UserNotFoundError,
)
from app.models.session import AnalysisSession, Short
from app.models.user import User
from app.schemas.clip import GenerateClipsRequest, GenerateClipsResponse
from app.tasks.generate_short_task import generate_short
from app.utils.youtube import validate_youtube_url

logger = logging.getLogger(__name__)

MAX_CLIPS_PER_VIDEO = 10
FREE_RECLIP_WINDOW_HOURS = 24


class ClipService:

    @staticmethod
    def generate_clips(
        db: Session,
        user_id: str,
        request: GenerateClipsRequest,
    ) -> GenerateClipsResponse:
        """
        Generate manual clips from a YouTube video.

        1. Validate URL
        2. Check free re-clip eligibility
        3. Check & deduct manual clip minutes
        4. Create AnalysisSession (source_type="manual")
        5. Create Short records
        6. Enqueue Celery tasks
        """
        # 1. Validate YouTube URL
        is_valid, video_id, error_msg = validate_youtube_url(request.youtube_url)
        if not is_valid or not video_id:
            raise InvalidURLError(error_msg or "Invalid YouTube URL")

        user = db.get(User, user_id)
        if not user:
            raise UserNotFoundError()

        # 2. Check free re-clip eligibility
        is_free_reclip = False
        if request.ai_session_id:
            is_free_reclip = ClipService._check_free_reclip(
                db, user_id, video_id, request.ai_session_id
            )

        # 3. Calculate total duration
        total_duration = sum(clip.duration for clip in request.clips)
        total_minutes = total_duration / 60.0

        if total_minutes > 120:
            raise InvalidStateError(
                f"Total clip duration {total_minutes:.1f} min exceeds the 120 min limit."
            )

        # 4. Check clip count for this video (existing + new <= 10)
        existing_clip_count = db.execute(
            select(func.count(Short.id))
            .join(AnalysisSession, Short.session_id == AnalysisSession.id)
            .where(
                AnalysisSession.video_id == video_id,
                AnalysisSession.user_id == user_id,
            )
        ).scalar() or 0

        if existing_clip_count + len(request.clips) > MAX_CLIPS_PER_VIDEO:
            raise InvalidStateError(
                f"Maximum {MAX_CLIPS_PER_VIDEO} clips per video. "
                f"You have {existing_clip_count} existing clips."
            )

        # 5. Determine watermark status.
        # New pricing model:
        #   - Pro/Pro Max → always watermark-free
        #   - Free re-clip (AI-analyzed with paid/PAYG credits) → watermark-free
        #   - Everyone else → watermarked (still always free, no deduction)
        minutes_deducted = 0.0
        if user.plan_tier in ("pro", "pro_max") or is_free_reclip:
            is_watermarked = False
            credits_source = "paid" if user.plan_tier in ("pro", "pro_max") else "payg"
        else:
            is_watermarked = True
            credits_source = "free"

        session = AnalysisSession(
            user_id=user_id,
            youtube_url=request.youtube_url,
            video_id=video_id,
            video_title="",  # Will be populated by first task if needed
            video_duration_seconds=0.0,
            niche="Generic",
            language="English",
            status="generating_shorts",
            source_type="manual",
            minutes_charged=0.0,
            credits_source=credits_source,
            is_watermarked=is_watermarked,
        )
        db.add(session)
        db.flush()  # Get session.id

        # 6. No credit deduction — manual clips are always free.
        # (Watermark removal is free for Pro users and re-clips from paid AI sessions.)

        # 7. Create Short records
        shorts = []
        for clip in request.clips:
            short = Short(
                session_id=session.id,
                hook_id=None,  # Manual clips have no hook
                source_type="manual",
                status="queued",
                caption_style=request.caption_style,
                aspect_ratio=request.aspect_ratio,
                start_seconds_override=clip.start_time,
                end_seconds_override=clip.end_time,
                is_watermarked=is_watermarked,
            )
            db.add(short)
            shorts.append(short)

        db.commit()

        # 8. Enqueue Celery tasks
        task_ids = []
        for short in shorts:
            db.refresh(short)
            task = generate_short.delay(short.id)
            short.task_id = task.id
            task_ids.append(task.id)

        db.commit()

        return GenerateClipsResponse(
            session_id=session.id,
            short_ids=[str(s.id) for s in shorts],
            task_ids=task_ids,
            total_duration_seconds=total_duration,
            minutes_deducted=minutes_deducted,
            is_free_reclip=is_free_reclip,
        )

    @staticmethod
    def _check_free_reclip(
        db: Session, user_id: str, video_id: str, ai_session_id: str
    ) -> bool:
        """Check if user qualifies for free re-clip from a previous AI analysis."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=FREE_RECLIP_WINDOW_HOURS)

        ai_session = db.get(AnalysisSession, ai_session_id)
        if not ai_session:
            return False

        # Handle timezone-naive datetimes from SQLite
        created = ai_session.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        return (
            ai_session.user_id == user_id
            and ai_session.video_id == video_id
            and ai_session.source_type == "ai"
            and ai_session.status in ("completed", "hooks_ready")
            and not ai_session.is_watermarked  # Only paid/PAYG analyses qualify
            and created >= cutoff
        )
