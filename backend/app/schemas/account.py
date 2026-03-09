"""
Schemas para contas de trading.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(default="USD", max_length=10)
    platform: str = Field(default="manual", max_length=30)
    is_demo: bool = False
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0)
    current_balance: Decimal | None = None  # se None, usa initial_balance
    leverage: int | None = None
    external_account_id: str | None = None


class AccountUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    currency: str | None = None
    platform: str | None = None
    is_demo: bool | None = None
    current_balance: Decimal | None = None
    leverage: int | None = None
    closed_at: datetime | None = None


class AccountRead(BaseModel):
    id: UUID
    workspace_id: UUID
    broker_connection_id: UUID | None
    external_account_id: str | None
    name: str
    currency: str
    platform: str
    is_demo: bool
    initial_balance: Decimal
    current_balance: Decimal
    leverage: int | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None

    model_config = {"from_attributes": True}
