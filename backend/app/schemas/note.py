"""
Schemas para notas diárias.
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DailyNoteCreate(BaseModel):
    date: date
    title: str = Field(..., min_length=1, max_length=255)
    content: str | None = None
    mood: int | None = Field(None, ge=1, le=5)
    account_id: UUID | None = None


class DailyNoteUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None
    mood: int | None = Field(None, ge=1, le=5)
    account_id: UUID | None = None


class DailyNoteRead(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    account_id: UUID | None
    date: date
    title: str
    content: str | None
    mood: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
