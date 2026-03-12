from typing import Optional, List
from datetime import date
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_trades: int
    win_trades: int
    loss_trades: int
    win_rate: float
    total_pnl: float
    best_trade: float
    worst_trade: float
    current_balance: float
    initial_balance: float
    monthly_goal: Optional[float] = None
    goal_progress: float


class MonthlyData(BaseModel):
    month: int
    year: int
    total_trades: int
    win_trades: int
    loss_trades: int
    win_rate: float
    total_pnl: float


class PairPerformance(BaseModel):
    pair: str
    total_trades: int
    win_trades: int
    win_rate: float
    total_pnl: float


class WeekdayPerformance(BaseModel):
    weekday: int
    weekday_name: str
    total_trades: int
    win_rate: float
    total_pnl: float


class TopTrade(BaseModel):
    id: str
    date: date
    pair: str
    direction: str
    pnl: float
    result: str
