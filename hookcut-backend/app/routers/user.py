"""
User router — thin HTTP adapter.

All business logic lives in UserService. This module only:
  1. Extracts request data
  2. Calls UserService
  3. Returns the response schema
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user_id
from app.exceptions import HookCutError
from app.schemas.billing import BalanceResponse
from app.services.user_service import UserService


class CurrencyUpdateRequest(BaseModel):
    currency: str


router = APIRouter()


@router.get("/user/balance", response_model=BalanceResponse)
async def get_balance(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current credit balance for the authenticated user."""
    return UserService.get_balance(db, user_id)


@router.get("/user/history")
async def get_history(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get past analysis sessions for the authenticated user."""
    return UserService.get_history(db, user_id, page, per_page)


@router.get("/user/profile")
async def get_profile(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get user profile."""
    try:
        return UserService.get_profile(db, user_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.patch("/user/currency")
async def update_currency(
    body: CurrencyUpdateRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Change preferred currency."""
    try:
        return UserService.update_currency(db, user_id, body.currency)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
