"""
Schemas para perfil, planos, indicações e IA.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# --- Plan ---


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(basic|intermediate|advanced)$")
    price: Decimal = Field(..., gt=0)
    max_accounts: int = Field(default=1, gt=0)
    features: dict = Field(..., min_items=1)
    is_active: bool = Field(default=True)


class PlanUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    type: str | None = Field(None, pattern="^(basic|intermediate|advanced)$")
    price: Decimal | None = Field(None, gt=0)
    max_accounts: int | None = Field(None, gt=0)
    features: dict | None = None
    is_active: bool | None = None


class PlanRead(BaseModel):
    id: UUID
    name: str
    type: str
    price: Decimal
    max_accounts: int
    features: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- UserPlan ---


class UserPlanCreate(BaseModel):
    plan_id: UUID
    status: str = Field(default="active", pattern="^(active|inactive|cancelled)$")
    validade: datetime | None = None


class UserPlanUpdate(BaseModel):
    status: str | None = Field(None, pattern="^(active|inactive|cancelled)$")
    validade: datetime | None = None


class UserPlanRead(BaseModel):
    id: UUID
    user_id: UUID
    plan_id: UUID
    status: str
    validade: datetime | None
    created_at: datetime
    updated_at: datetime
    plan: PlanRead | None = None

    model_config = {"from_attributes": True}


# --- UserProfile ---


class UserProfileCreate(BaseModel):
    foto_url: str | None = None
    telefone: str | None = Field(None, max_length=20)
    cidade: str | None = Field(None, max_length=100)
    pais: str | None = Field(None, max_length=100)
    data_nascimento: datetime | None = None
    redes_sociais: dict | None = None
    preferencias: dict | None = None
    cpf: str | None = Field(None, max_length=20)


class UserProfileUpdate(BaseModel):
    foto_url: str | None = None
    telefone: str | None = Field(None, max_length=20)
    cidade: str | None = Field(None, max_length=100)
    pais: str | None = Field(None, max_length=100)
    data_nascimento: datetime | None = None
    redes_sociais: dict | None = None
    preferencias: dict | None = None
    cpf: str | None = Field(None, max_length=20)


class UserProfileRead(BaseModel):
    id: UUID
    user_id: UUID
    foto_url: str | None
    telefone: str | None
    cidade: str | None
    pais: str | None
    data_nascimento: datetime | None
    redes_sociais: dict | None
    preferencias: dict | None
    cpf: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- ReferralCode ---


class ReferralCodeCreate(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=20)
    max_desconto: Decimal = Field(default=100, ge=0, le=100)


class ReferralCodeUpdate(BaseModel):
    max_desconto: Decimal | None = Field(None, ge=0, le=100)
    is_active: bool | None = None


class ReferralCodeRead(BaseModel):
    id: UUID
    codigo: str
    user_id: UUID
    desconto_total: Decimal
    max_desconto: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Referral ---


class ReferralCreate(BaseModel):
    referral_code_id: UUID


class ReferralUpdate(BaseModel):
    status: str | None = Field(None, pattern="^(pending|completed|cancelled)$")
    desconto_gerado: Decimal | None = Field(None, ge=0)
    completed_at: datetime | None = None


class ReferralRead(BaseModel):
    id: UUID
    referrer_id: UUID
    referred_id: UUID
    referral_code_id: UUID
    status: str
    desconto_gerado: Decimal
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- AIConversation ---


class AIConversationCreate(BaseModel):
    workspace_id: UUID
    title: str | None = Field(None, max_length=200)
    messages: dict = Field(..., min_items=1)


class AIConversationUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    messages: dict | None = None


class AIConversationRead(BaseModel):
    id: UUID
    user_id: UUID
    workspace_id: UUID
    title: str | None
    messages: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Dashboard Stats ---


class DashboardStats(BaseModel):
    total_balance: Decimal
    total_pnl: Decimal
    total_trades: int
    win_rate: int
    monthly_data: list[dict]
    avg_monthly: Decimal
    pnl_variation: Decimal
    pair_data: list[dict]
    dow_data: list[dict]
    best_dow: dict
    week_data: list[dict]
    distribution: list[dict]
    balance_evo_sampled: list[dict]
    heatmap_data: list[dict]
    top5_best: list[dict]
    top5_worst: list[dict]
    account_summary: list[dict]
    week_trades: list[dict]
    week_pnl_total: Decimal
    wr_spark: list[int]
    monthly_pnls: list[Decimal]


class WeeklyReportData(BaseModel):
    week_pnl: Decimal
    prev_pnl: Decimal
    week_win_rate: int
    diff_pnl: Decimal
    highlights: dict | None
    chart_data: list[dict]
    history: list[dict]
    week_trades_count: int


class GPScoreData(BaseModel):
    gp_score: Decimal
    win_rate: int
    profit_factor: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    consistency_score: Decimal
    monthly_growth: Decimal


class GoalNotification(BaseModel):
    type: str  # "monthly" or "biweekly"
    achieved: bool
    percentage: Decimal
    current_amount: Decimal
    target_amount: Decimal
    remaining_days: int | None = None
