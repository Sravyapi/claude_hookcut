"""
NextAuth.js JWT verification middleware.
V0: Bypassed (FEATURE_V0_MODE=true returns a default user).
V1: Verifies NextAuth JWT from Authorization header using shared secret.
"""
import logging
import jwt
from fastapi import Request, HTTPException
from app.config import get_settings

logger = logging.getLogger(__name__)


async def get_authenticated_user_id(request: Request) -> str:
    """Extract and verify user ID from request."""
    settings = get_settings()

    if settings.FEATURE_V0_MODE:
        return "v0_local_user"

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]

    if not settings.NEXTAUTH_SECRET:
        logger.error("NEXTAUTH_SECRET not configured")
        raise HTTPException(status_code=500, detail="Auth not configured")

    try:
        payload = jwt.decode(
            token,
            settings.NEXTAUTH_SECRET,
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
