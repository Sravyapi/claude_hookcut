import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # Clerk user ID or local ID
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")  # "INR" or "USD"
    plan_tier: Mapped[str] = mapped_column(String(20), default="free")  # "free", "lite", "pro"

    role: Mapped[str] = mapped_column(String(20), default="user")  # "user" or "admin"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    credit_balance: Mapped["CreditBalance"] = relationship(back_populates="user", uselist=False)
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")


class CreditBalance(Base):
    __tablename__ = "credit_balances"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    paid_minutes_remaining: Mapped[float] = mapped_column(Float, default=0.0)
    paid_minutes_total: Mapped[float] = mapped_column(Float, default=0.0)
    free_minutes_remaining: Mapped[float] = mapped_column(Float, default=120.0)
    free_minutes_total: Mapped[float] = mapped_column(Float, default=120.0)
    payg_minutes_remaining: Mapped[float] = mapped_column(Float, default=0.0)
    last_free_reset: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="credit_balance")

    @property
    def total_available(self) -> float:
        return self.paid_minutes_remaining + self.payg_minutes_remaining + self.free_minutes_remaining


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    plan_tier: Mapped[str] = mapped_column(String(20))  # "lite", "pro"
    currency: Mapped[str] = mapped_column(String(3))
    provider: Mapped[str] = mapped_column(String(20))  # "stripe", "razorpay"
    provider_subscription_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_period_start: Mapped[datetime] = mapped_column(DateTime)
    current_period_end: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="subscriptions")
