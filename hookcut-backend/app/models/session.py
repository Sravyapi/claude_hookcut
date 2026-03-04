import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    youtube_url: Mapped[str] = mapped_column(String(500))
    video_id: Mapped[str] = mapped_column(String(20), index=True)
    video_title: Mapped[str] = mapped_column(String(500), default="")
    video_duration_seconds: Mapped[float] = mapped_column(Float)
    niche: Mapped[str] = mapped_column(String(50))
    language: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # Status values: pending, fetching_transcript, analyzing,
    #                hooks_ready, generating_shorts, completed, failed
    transcript_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    transcript_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    minutes_charged: Mapped[float] = mapped_column(Float, default=0.0)
    credits_source: Mapped[str] = mapped_column(String(20), default="free")
    # credits_source: "paid", "free", "payg", "mixed"
    is_watermarked: Mapped[bool] = mapped_column(Boolean, default=True)
    credits_refunded: Mapped[bool] = mapped_column(Boolean, default=False)
    regeneration_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Track credit breakdown for refunds
    paid_minutes_used: Mapped[float] = mapped_column(Float, default=0.0)
    payg_minutes_used: Mapped[float] = mapped_column(Float, default=0.0)
    free_minutes_used: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    hooks: Mapped[list["Hook"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    shorts: Mapped[list["Short"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Hook(Base):
    __tablename__ = "hooks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), index=True
    )
    rank: Mapped[int] = mapped_column(Integer)
    hook_text: Mapped[str] = mapped_column(Text)
    start_time: Mapped[str] = mapped_column(String(20))
    end_time: Mapped[str] = mapped_column(String(20))
    start_seconds: Mapped[float] = mapped_column(Float)
    end_seconds: Mapped[float] = mapped_column(Float)
    hook_type: Mapped[str] = mapped_column(String(50))
    funnel_role: Mapped[str] = mapped_column(String(30))
    scores: Mapped[dict] = mapped_column(JSON)
    attention_score: Mapped[float] = mapped_column(Float)
    platform_dynamics: Mapped[str] = mapped_column(Text, default="")
    viewer_psychology: Mapped[str] = mapped_column(Text, default="")
    improvement_suggestion: Mapped[str] = mapped_column(Text, default="")
    is_composite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    session: Mapped["AnalysisSession"] = relationship(back_populates="hooks")
    shorts: Mapped[list["Short"]] = relationship(back_populates="hook")


class Short(Base):
    __tablename__ = "shorts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_sessions.id", ondelete="CASCADE"), index=True
    )
    hook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("hooks.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="queued")
    # Status values: queued, downloading, processing, uploading, ready, failed, expired
    caption_style: Mapped[str] = mapped_column(String(20), default="clean")
    start_seconds_override: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    end_seconds_override: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_watermarked: Mapped[bool] = mapped_column(Boolean, default=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    cleaned_captions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_file_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_file_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    download_url_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    session: Mapped["AnalysisSession"] = relationship(back_populates="shorts")
    hook: Mapped["Hook"] = relationship(back_populates="shorts")
