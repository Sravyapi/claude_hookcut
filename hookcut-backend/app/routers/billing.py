"""
Billing router — thin HTTP adapter.

All business logic lives in BillingService. This module only:
  1. Extracts request data
  2. Calls BillingService
  3. Returns the response schema
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user_id
from app.exceptions import HookCutError
from app.schemas.billing import PlansResponse
from app.services.billing_service import BillingService

router = APIRouter()


@router.get("/billing/plans", response_model=PlansResponse)
async def get_plans(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get available subscription plans for user's currency."""
    return BillingService.get_plans(db, user_id)


@router.post("/billing/checkout")
async def create_checkout(
    plan_tier: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a checkout session for subscription purchase."""
    try:
        result = BillingService.create_checkout(db, user_id, plan_tier)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return {"checkout_url": result.checkout_url, "session_id": result.session_id}


@router.post("/billing/payg")
async def purchase_payg(
    minutes: int = 100,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Purchase PAYG minutes."""
    try:
        result = BillingService.create_payg_checkout(db, user_id, minutes)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return {"checkout_url": result.checkout_url, "session_id": result.session_id}


# --- User sync endpoint (called by frontend after NextAuth login) ---

@router.post("/auth/sync")
async def sync_user(
    email: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Ensure user exists in backend after NextAuth login."""
    return BillingService.sync_user(db, user_id, email)


# --- V0-only endpoints for testing ---

@router.post("/billing/v0-grant")
async def v0_grant_credits(
    paid_minutes: float = 0,
    payg_minutes: float = 0,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """V0 only: Grant test credits without payment."""
    try:
        return BillingService.v0_grant_credits(db, user_id, paid_minutes, payg_minutes)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# --- Webhook handlers ---

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        return BillingService.handle_stripe_webhook(db, payload, sig)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Razorpay webhook events."""
    payload = await request.body()
    sig = request.headers.get("x-razorpay-signature", "")

    try:
        return BillingService.handle_razorpay_webhook(db, payload, sig)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
