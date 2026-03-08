"""
Shorts router — thin HTTP adapter.

All business logic lives in ShortsService. This module only:
  1. Extracts request data
  2. Calls ShortsService
  3. Returns the response schema
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user_id
from app.exceptions import HookCutError
from app.models.session import Short
from app.schemas.shorts import ShortResponse, ShortDownloadResponse
from app.services.shorts_service import ShortsService

router = APIRouter()


@router.get("/storage/{file_key:path}")
def serve_local_file(
    file_key: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Serve files from local storage (V0 only). In production, R2 presigned URLs are used."""
    # Verify the file_key belongs to a Short owned by the requesting user
    short = db.execute(
        select(Short).where(
            (Short.video_file_key == file_key) | (Short.thumbnail_file_key == file_key)
        )
    ).scalar_one_or_none()
    if not short or not short.session or short.session.user_id != user_id:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        path, media_type = ShortsService.serve_local_file(file_key)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return FileResponse(path, media_type=media_type)


@router.get("/shorts/{short_id}", response_model=ShortResponse)
def get_short(
    short_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get Short details including status and download URL."""
    short = db.get(Short, short_id)
    if not short or not short.session or short.session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Short not found")

    try:
        return ShortsService.get_short(db, short_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/shorts/{short_id}/download", response_model=ShortDownloadResponse)
def download_short(
    short_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Generate a fresh presigned download URL and log the download event."""
    short = db.get(Short, short_id)
    if not short or not short.session or short.session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Short not found")

    try:
        return ShortsService.download_short(db, short_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/shorts/{short_id}/discard")
def discard_short(
    short_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Mark a Short as discarded (user chose not to download)."""
    short = db.get(Short, short_id)
    if not short or not short.session or short.session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Short not found")

    try:
        return ShortsService.discard_short(db, short_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
