from typing import Generator
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.models.base import get_session_factory
from app.middleware.auth import get_authenticated_user_id


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a database session."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Direct session factory for use in Celery tasks (non-generator)."""
    return get_session_factory()()


async def get_current_user_id(request: Request) -> str:
    """FastAPI dependency: extracts authenticated user ID from request."""
    return await get_authenticated_user_id(request)


async def get_admin_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """FastAPI dependency: requires authenticated admin user. Returns User model."""
    from app.models.user import User
    user_id = await get_current_user_id(request)
    user = db.get(User, user_id)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
