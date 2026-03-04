from pydantic import BaseModel, field_validator
from typing import Literal


class BalanceResponse(BaseModel):
    paid_minutes_remaining: float
    paid_minutes_total: float
    free_minutes_remaining: float
    free_minutes_total: float
    payg_minutes_remaining: float
    total_available: float


class PlanInfo(BaseModel):
    tier: Literal["free", "lite", "pro"]
    price_display: str
    watermark_free_minutes: int
    currency: Literal["USD", "INR"]

    @field_validator("watermark_free_minutes")
    @classmethod
    def validate_watermark_free_minutes(cls, v: int) -> int:
        if v < 0:
            raise ValueError("watermark_free_minutes must be >= 0")
        return v


class PlansResponse(BaseModel):
    current_tier: str
    currency: Literal["USD", "INR"]
    plans: list[PlanInfo]
