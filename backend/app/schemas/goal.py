from typing import Optional
from pydantic import BaseModel


class GoalUpdate(BaseModel):
    monthly_goal: Optional[float] = None
    meta: Optional[float] = None


class GoalResponse(BaseModel):
    account_id: str
    account_name: str
    monthly_goal: Optional[float]
    meta: Optional[float]
    current_balance: float
    monthly_pnl: float
    monthly_progress: float
    total_progress: float
