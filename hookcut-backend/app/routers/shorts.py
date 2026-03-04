"""
Shorts router — thin HTTP adapter.

All business logic lives in ShortsService. This module only:
  1. Extracts request data
  2. Calls ShortsService
  3. Returns the response schema
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.exceptions import HookCutError
from app.schemas.shorts import ShortResponse, ShortDownloadResponse
from app.services.shorts_service import ShortsService

router = APIRouter()


@router.get("/storage/{file_key:path}")
def serve_local_file(file_key: str):
    """Serve files from local storage (V0 only). In production, R2 presigned URLs are used."""
    try:
        path, media_type = ShortsService.serve_local_file(file_key)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return FileResponse(path, media_type=media_type)


@router.get("/shorts/{short_id}", response_model=ShortResponse)
def get_short(short_id: str, db: Session = Depends(get_db)):
    """Get Short details including status and download URL."""
    try:
        return ShortsService.get_short(db, short_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/shorts/{short_id}/download", response_model=ShortDownloadResponse)
def download_short(short_id: str, db: Session = Depends(get_db)):
    """Generate a fresh presigned download URL and log the download event."""
    try:
        return ShortsService.download_short(db, short_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/shorts/{short_id}/discard")
def discard_short(short_id: str, db: Session = Depends(get_db)) -> dict:
    """Mark a Short as discarded (user chose not to download)."""
    try:
        return ShortsService.discard_short(db, short_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
