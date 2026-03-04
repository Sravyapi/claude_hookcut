import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(30))
    # Types: credit_deduction, credit_refund, subscription_payment,
    #        payg_purchase, regeneration_fee
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    minutes_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    money_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # In smallest currency unit (paisa/cents)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    provider_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
