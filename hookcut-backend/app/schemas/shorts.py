from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ShortResponse(BaseModel):
    id: str
    hook_id: str
    status: str
    is_watermarked: bool
    title: Optional[str] = None
    cleaned_captions: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    download_url_expires_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    error_message: Optional[str] = None


class ShortDownloadResponse(BaseModel):
    download_url: str
    expires_at: datetime
