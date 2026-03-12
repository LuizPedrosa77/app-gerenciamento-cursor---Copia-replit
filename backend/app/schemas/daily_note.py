from datetime import datetime, date
from pydantic import BaseModel


class DailyNoteCreate(BaseModel):
    date: date
    note: str
    account_id: str


class DailyNoteUpdate(BaseModel):
    note: str


class DailyNoteResponse(BaseModel):
    id: str
    date: date
    note: str
    account_id: str
    created_at: datetime
    updated_at: datetime
