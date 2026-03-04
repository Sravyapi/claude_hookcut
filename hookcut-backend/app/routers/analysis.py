"""
Analysis router — thin HTTP adapter.

All business logic lives in AnalyzeService. This module only:
  1. Extracts request data
  2. Calls AnalyzeService
  3. Returns the response schema
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user_id
from app.exceptions import HookCutError
from app.middleware.rate_limit import get_rate_limiter
from app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    VideoValidateRequest,
    VideoValidateResponse,
    RegenerateResponse,
    SelectHooksRequest,
    SelectHooksResponse,
)
from app.schemas.hooks import HooksListResponse, HookResponse, HookScores
from app.services.analyze_service import AnalyzeService

router = APIRouter()

rate_limiter = get_rate_limiter()


@router.post("/validate-url", response_model=VideoValidateResponse)
def validate_url(req: VideoValidateRequest):
    """Validate YouTube URL and return video metadata."""
    return AnalyzeService.validate_url(req)


@router.post("/analyze", response_model=AnalyzeResponse)
async def start_analysis(
    req: AnalyzeRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Start hook analysis for a YouTube video.
    Credits deducted at this point. Dispatches async Celery task.
    """
    rate_limiter.check(user_id, "analyze", limit=10, window_seconds=900)

    try:
        result = AnalyzeService.start_analysis(
            db=db,
            user_id=user_id,
            youtube_url=req.youtube_url,
            niche=req.niche,
            language=req.language,
        )
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return AnalyzeResponse(**result)


@router.get("/sessions/{session_id}/hooks", response_model=HooksListResponse)
def get_hooks(session_id: str, db: Session = Depends(get_db)):
    """Get the 5 hooks for a session."""
    try:
        data = AnalyzeService.get_hooks(db=db, session_id=session_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    session = data["session"]
    hooks = data["hooks"]

    return HooksListResponse(
        session_id=session_id,
        status=session.status,
        regeneration_count=session.regeneration_count,
        hooks=[
            HookResponse(
                id=h.id,
                rank=h.rank,
                hook_text=h.hook_text,
                start_time=h.start_time,
                end_time=h.end_time,
                hook_type=h.hook_type,
                funnel_role=h.funnel_role,
                scores=HookScores(**h.scores) if h.scores else HookScores(),
                attention_score=h.attention_score,
                platform_dynamics=h.platform_dynamics,
                viewer_psychology=h.viewer_psychology,
                improvement_suggestion=h.improvement_suggestion or "",
                is_composite=h.is_composite,
                is_selected=h.is_selected,
            )
            for h in hooks
        ],
    )


@router.post("/sessions/{session_id}/regenerate", response_model=RegenerateResponse)
def regenerate_hooks(
    session_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Regenerate hooks. 1st free, 2nd+ charged.
    Replaces all previous hooks.
    """
    rate_limiter.check(user_id, "regenerate", limit=5, window_seconds=900)

    try:
        result = AnalyzeService.regenerate_hooks(db=db, session_id=session_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return RegenerateResponse(**result)


@router.post("/sessions/{session_id}/select-hooks", response_model=SelectHooksResponse)
def select_hooks(
    session_id: str,
    req: SelectHooksRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Select 1-3 hooks to generate Shorts from."""
    rate_limiter.check(user_id, "select_hooks", limit=10, window_seconds=900)

    try:
        result = AnalyzeService.select_hooks(
            db=db,
            session_id=session_id,
            hook_ids=req.hook_ids,
            caption_style=req.caption_style,
            time_overrides=req.time_overrides,
        )
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return SelectHooksResponse(**result)
