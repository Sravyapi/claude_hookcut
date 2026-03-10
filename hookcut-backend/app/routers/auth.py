"""
Auth router — email/password registration and login.

Thin HTTP adapter: extracts request data, delegates to AuthService, returns response.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, RoleLookupRequest, RoleLookupResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    return AuthService.register(db, req.email, req.password, req.name)


@router.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate an existing user with email and password."""
    return AuthService.login(db, req.email, req.password)


@router.post("/auth/role", response_model=RoleLookupResponse)
async def lookup_role(req: RoleLookupRequest, db: Session = Depends(get_db)):
    """Look up a user's role by email. Used server-side by NextAuth JWT callback for Google OAuth."""
    return {"role": AuthService.get_role_by_email(db, req.email)}
