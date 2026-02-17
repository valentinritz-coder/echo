from datetime import datetime

from pydantic import BaseModel


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


class ErrorResponse(BaseModel):
    error: dict[str, str]
