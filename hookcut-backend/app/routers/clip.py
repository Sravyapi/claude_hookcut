"""Router for manual clip generation."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user_id
from app.schemas.clip import GenerateClipsRequest, GenerateClipsResponse
from app.services.clip_service import ClipService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clips", tags=["clips"])


@router.post("/generate", response_model=GenerateClipsResponse)
async def generate_clips(
    request_body: GenerateClipsRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generate manual clips from a YouTube video. No rate limit — credits gate usage."""
    return ClipService.generate_clips(db, user_id, request_body)
