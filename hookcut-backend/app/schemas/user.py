from pydantic import BaseModel, Field


class CurrencyUpdateRequest(BaseModel):
    currency: str = Field(..., max_length=3, pattern=r"^[A-Z]{3}$")
