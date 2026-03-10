"""
Billing router — thin HTTP adapter.

All business logic lives in BillingService. This module only:
  1. Extracts request data
  2. Calls BillingService
  3. Returns the response schema
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from typing import Optional

from app.dependencies import get_db, get_current_user_id, get_optional_user_id
from app.exceptions import HookCutError
from app.schemas.billing import PlansResponse, BalanceResponse
from app.services.billing_service import BillingService
from app.services.credit_manager import CreditManager


class CheckoutRequest(BaseModel):
    plan_tier: str


class PaygRequest(BaseModel):
    minutes: int = 100


class SyncUserRequest(BaseModel):
    email: EmailStr


router = APIRouter()


@router.get("/billing/plans", response_model=PlansResponse)
async def get_plans(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    """Get available subscription plans. Returns user's currency if authenticated, USD otherwise."""
    return BillingService.get_plans(db, user_id)


@router.post("/billing/checkout")
async def create_checkout(
    req: CheckoutRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a checkout session for subscription purchase."""
    try:
        result = BillingService.create_checkout(db, user_id, req.plan_tier)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return {"checkout_url": result.checkout_url, "session_id": result.session_id}


@router.post("/billing/payg")
async def purchase_payg(
    req: PaygRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Purchase PAYG minutes."""
    try:
        result = BillingService.create_payg_checkout(db, user_id, req.minutes)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    return {"checkout_url": result.checkout_url, "session_id": result.session_id}


@router.post("/billing/free-topup", response_model=BalanceResponse)
async def claim_free_topup(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Claim a free top-up of 120 watermarked minutes (limited per account)."""
    try:
        balance = CreditManager(db).claim_free_topup(user_id)
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    return balance


# --- User sync endpoint (called by frontend after NextAuth login) ---

@router.post("/auth/sync")
async def sync_user(
    req: SyncUserRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Ensure user exists in backend after NextAuth login."""
    return BillingService.sync_user(db, user_id, str(req.email))


# --- Webhook handlers ---

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    # HIGH-18: Reject immediately if signature header is absent (before reading body)
    sig = request.headers.get("stripe-signature")
    if not sig:
        return JSONResponse({"detail": "Missing stripe-signature header"}, status_code=400)

    payload = await request.body()

    try:
        # HIGH-19: stripe.Webhook.construct_event is a blocking HMAC call — run it
        # in a thread pool so it does not block the async event loop.
        import anyio
        result = await anyio.to_thread.run_sync(
            lambda: BillingService.handle_stripe_webhook(db, payload, sig)
        )
        return result
    except HookCutError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Razorpay webhook events."""
    payload = await request.body()
    sig = request.headers.get("x-razorpay-signature", "")

    if not sig:
        return JSONResponse({"detail": "Missing signature"}, status_code=400)

    try:
        return BillingService.handle_razorpay_webhook(db, payload, sig)
    except HookCutError as e:
        # HIGH-32: Return 400 on signature/validation failures rather than propagating as 500
        if e.status_code in (400, 401, 403):
            return JSONResponse({"detail": "Invalid signature"}, status_code=400)
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception:
        # HIGH-32: Catch unexpected errors from signature verification and return 400
        logger.exception("Razorpay webhook error")
        return JSONResponse({"detail": "Invalid signature"}, status_code=400)
