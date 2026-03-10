"""Schemas for the Manual Clipper feature."""

from pydantic import BaseModel, field_validator
from typing import Literal, Optional


class ClipSegment(BaseModel):
    start_time: float  # seconds
    end_time: float    # seconds

    @field_validator("start_time", "end_time")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("time must be non-negative")
        return v

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class GenerateClipsRequest(BaseModel):
    youtube_url: str
    clips: list[ClipSegment]  # 1-10 items
    caption_style: Literal["clean", "bold", "neon", "minimal"] = "clean"
    captions_enabled: bool = True
    audio_normalization: bool = True
    aspect_ratio: Literal["9:16", "1:1", "4:5"] = "9:16"
    ai_session_id: Optional[str] = None  # for free re-clip flow

    @field_validator("clips")
    @classmethod
    def validate_clip_count(cls, v):
        if len(v) == 0:
            raise ValueError("At least one clip is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 clips per video")
        return v

    @field_validator("clips")
    @classmethod
    def validate_min_duration(cls, v):
        for clip in v:
            if clip.duration < 3.0:
                raise ValueError(
                    f"Clip duration must be at least 3 seconds (got {clip.duration:.1f}s)"
                )
        return v

    @field_validator("clips")
    @classmethod
    def validate_max_source_duration(cls, v):
        for clip in v:
            if clip.end_time > 7200:
                raise ValueError("Clips cannot extend beyond 2 hours into the video")
        return v


class GenerateClipsResponse(BaseModel):
    session_id: str
    short_ids: list[str]  # one per clip, same order as input clips
    task_ids: list[str]  # Celery task IDs, same order
    total_duration_seconds: float
    minutes_deducted: float
    is_free_reclip: bool
