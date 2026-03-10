"""
Auth router — email/password registration and login.

Thin HTTP adapter: extracts request data, delegates to AuthService, returns response.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.middleware.rate_limit import get_rate_limiter
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, RoleLookupRequest, RoleLookupResponse
from app.services.auth_service import AuthService

router = APIRouter()
rate_limiter = get_rate_limiter()


@router.post("/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(f"ip:{client_ip}", "auth_register", limit=10, window_seconds=900, request=request)
    return AuthService.register(db, req.email, req.password, req.name)


@router.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate an existing user with email and password."""
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(f"ip:{client_ip}", "auth_login", limit=10, window_seconds=900, request=request)
    return AuthService.login(db, req.email, req.password)


@router.post("/auth/role", response_model=RoleLookupResponse)
async def lookup_role(req: RoleLookupRequest, request: Request, db: Session = Depends(get_db)):
    """Look up a user's role by email. Used server-side by NextAuth JWT callback for Google OAuth."""
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(f"ip:{client_ip}", "auth_role", limit=30, window_seconds=900, request=request)
    return {"role": AuthService.get_role_by_email(db, req.email)}
