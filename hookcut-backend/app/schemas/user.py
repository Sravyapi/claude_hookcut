from pydantic import BaseModel


class CurrencyUpdateRequest(BaseModel):
    currency: str
