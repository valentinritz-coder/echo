import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Entry(Base):
    __tablename__ = "entries"
    __table_args__ = (
        CheckConstraint("ai_status IN ('none','pending','running','done','error')", name="ck_entries_ai_status"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    audio_path: Mapped[str] = mapped_column(String, nullable=False)
    audio_mime: Mapped[str] = mapped_column(String, nullable=False)
    audio_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ai_status: Mapped[str] = mapped_column(String, nullable=False, default="none", server_default="none")
    ai_last_run_id: Mapped[int | None] = mapped_column(ForeignKey("ai_runs.id", ondelete="SET NULL"), nullable=True)
    ai_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    audio_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    audio_duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)


class AiRun(Base):
    __tablename__ = "ai_runs"
    __table_args__ = (
        CheckConstraint("status IN ('pending','running','done','error')", name="ck_ai_runs_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entry_id: Mapped[str] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tasks_json: Mapped[str] = mapped_column(Text, nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String, nullable=False)
    audio_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stt_model: Mapped[str | None] = mapped_column(String, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String, nullable=True)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    keypoints_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
