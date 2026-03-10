"""
AuthService — email/password registration and login.

All new email/password users get a CreditBalance seeded with 120 free minutes.
OAuth users who later add a password have their hashed_password set on their
existing record; their credit balance is preserved.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import AuthenticationError, ConflictError
from app.models.user import User, CreditBalance

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @staticmethod
    def create_access_token(user_id: str, email: str) -> str:
        settings = get_settings()
        payload = {
            "sub": user_id,
            "email": email,
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        }
        return jwt.encode(payload, settings.NEXTAUTH_SECRET, algorithm="HS256")

    @staticmethod
    def register(db: Session, email: str, password: str, name: str) -> dict:
        existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing:
            if existing.hashed_password:
                raise ConflictError("Email already registered")
            # OAuth user adding a password — set it and update name if missing
            existing.hashed_password = AuthService.hash_password(password)
            if not existing.name:
                existing.name = name
            db.commit()
            token = AuthService.create_access_token(existing.id, existing.email)
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": existing.id,
                "email": existing.email,
                "name": existing.name or "",
                "role": existing.role or "user",
            }

        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            name=name,
            hashed_password=AuthService.hash_password(password),
            role="user",
        )
        db.add(user)
        db.flush()

        balance = CreditBalance(
            user_id=user_id,
            free_minutes_remaining=120.0,
            free_minutes_total=120.0,
            paid_minutes_remaining=0.0,
            paid_minutes_total=0.0,
            payg_minutes_remaining=0.0,
        )
        db.add(balance)
        db.commit()

        token = AuthService.create_access_token(user_id, email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id,
            "email": email,
            "name": name,
            "role": "user",
        }

    @staticmethod
    def get_role_by_email(db: Session, email: str) -> str:
        """Return the role for a user by email, defaulting to 'user' if not found."""
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        return (user.role or "user") if user else "user"

    @staticmethod
    def login(db: Session, email: str, password: str) -> dict:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user or not user.hashed_password:
            raise AuthenticationError("Invalid email or password")
        if not AuthService.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        token = AuthService.create_access_token(user.id, user.email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "name": user.name or "",
            "role": user.role or "user",
        }
