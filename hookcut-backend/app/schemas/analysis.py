from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from app.llm.prompts.constants import NICHES, LANGUAGES


class AnalyzeRequest(BaseModel):
    youtube_url: str
    niche: str = "Generic"
    language: str = "English"

    @field_validator("niche")
    @classmethod
    def validate_niche(cls, v: str) -> str:
        if v not in NICHES:
            raise ValueError(f"Invalid niche. Must be one of: {', '.join(NICHES.keys())}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in LANGUAGES:
            raise ValueError(f"Invalid language. Must be one of: {', '.join(LANGUAGES.keys())}")
        return v


class AnalyzeResponse(BaseModel):
    session_id: str
    task_id: str
    video_title: str
    video_duration_seconds: float
    minutes_charged: float
    is_watermarked: bool


class VideoValidateRequest(BaseModel):
    youtube_url: str
    # No URL format validation here — this endpoint's purpose is to accept
    # any URL and return {valid: False, error: "..."} for invalid ones.


class VideoValidateResponse(BaseModel):
    valid: bool
    video_id: Optional[str] = None
    title: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class RegenerateResponse(BaseModel):
    session_id: str
    task_id: str
    regeneration_count: int
    fee_charged: Optional[int] = None  # In smallest currency unit
    currency: Optional[str] = None

    @model_validator(mode="after")
    def validate_fee_currency_consistency(self) -> "RegenerateResponse":
        if self.fee_charged is not None and self.currency is None:
            raise ValueError("currency must be set when fee_charged is provided")
        return self


class TimeOverride(BaseModel):
    start_seconds: float
    end_seconds: float


class SelectHooksRequest(BaseModel):
    hook_ids: list[str]
    caption_style: str = "clean"
    time_overrides: dict[str, TimeOverride] = {}

    @field_validator("hook_ids")
    @classmethod
    def validate_hook_count(cls, v: list[str]) -> list[str]:
        if len(v) < 1 or len(v) > 3:
            raise ValueError("Must select between 1 and 3 hooks")
        return v

    @field_validator("hook_ids")
    @classmethod
    def validate_hook_ids_unique(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v):
            raise ValueError("hook_ids must not contain duplicates")
        return v

    @field_validator("caption_style")
    @classmethod
    def validate_caption_style(cls, v: str) -> str:
        from app.utils.ffmpeg_commands import VALID_CAPTION_STYLES
        if v not in VALID_CAPTION_STYLES:
            raise ValueError(f"Invalid caption style. Must be one of: {', '.join(VALID_CAPTION_STYLES)}")
        return v


class SelectHooksResponse(BaseModel):
    short_ids: list[str]
    task_ids: list[str]
