from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class QuestionOut(BaseModel):
    id: int
    text: str
    category: str
    is_active: bool


class EntryOut(BaseModel):
    id: str
    user_id: str
    question_id: int
    audio_mime: str
    audio_size: int
    created_at: datetime


class AIProcessRequest(BaseModel):
    tasks: list[Literal["transcribe", "summarize"]] = Field(default_factory=lambda: ["transcribe", "summarize"])
    force: bool = False
    pipeline_version: str = "v3.a"


class AIProcessReusedResponse(BaseModel):
    entry_id: str
    status: Literal["done"]
    last_run_id: int
    reused: Literal[True]


class AIProcessQueuedResponse(BaseModel):
    entry_id: str
    status: Literal["pending"]
    run_id: int
    reused: Literal[False]


class AIRunOut(BaseModel):
    id: int
    entry_id: str
    status: str
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    tasks: list[str]
    pipeline_version: str
    audio_sha256: str | None
    stt_model: str | None
    llm_model: str | None
    transcript_text: str | None
    transcript_json: Any | None
    summary_text: str | None
    keypoints_json: Any | None
    error_message: str | None
    metrics_json: Any | None


class EntryAIStatusOut(BaseModel):
    entry_id: str
    ai_status: str
    ai_last_run_id: int | None
    ai_updated_at: datetime | None
    last_run: AIRunOut | None


class ErrorResponse(BaseModel):
    error: dict[str, str]
