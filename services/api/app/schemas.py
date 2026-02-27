from datetime import datetime
from typing import Optional

import pydantic
from pydantic import BaseModel


class ORMBaseModel(BaseModel):
    if hasattr(pydantic, "ConfigDict"):
        model_config = pydantic.ConfigDict(from_attributes=True)
    else:

        class Config:
            orm_mode = True


class QuestionOut(ORMBaseModel):
    id: int
    text: str
    category: str
    is_active: bool


class EntryOut(ORMBaseModel):
    id: str
    user_id: str
    question_id: int
    audio_mime: str
    audio_size: int
    text_content: Optional[str] = None
    is_frozen: bool
    created_at: datetime


class EntryUpdateIn(BaseModel):
    question_id: Optional[int] = None
    text_content: Optional[str] = None


class EntriesListResponse(ORMBaseModel):
    items: list[EntryOut]
    next_offset: Optional[int] = None
    limit: int
    offset: int


class ErrorResponse(ORMBaseModel):
    error: dict[str, str]
