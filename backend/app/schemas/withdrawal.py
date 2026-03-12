from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class WithdrawalCreate(BaseModel):
    amount: float
    date: date
    notes: Optional[str] = None
    account_id: str


class WithdrawalResponse(BaseModel):
    id: str
    amount: float
    date: date
    notes: Optional[str]
    account_id: str
    created_at: datetime
