import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class LearningLog(Base):
    __tablename__ = "learning_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(30), index=True)
    # Event types: hook_presented, hook_selected, hook_not_selected,
    #              regeneration_triggered, short_downloaded, short_discarded
    hook_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    video_id: Mapped[str] = mapped_column(String(20), index=True)
    niche: Mapped[str] = mapped_column(String(50))
    language: Mapped[str] = mapped_column(String(50))
    event_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
