"""
Schemas para trades, tags e saques.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TradeTagRead(BaseModel):
    id: UUID
    name: str
    color: str | None

    model_config = {"from_attributes": True}


class TradeCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    side: str = Field(..., pattern="^(buy|sell)$")
    volume: Decimal = Field(..., gt=0)
    open_time: datetime
    close_time: datetime | None = None
    open_price: Decimal
    close_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    commission: Decimal = Field(default=Decimal("0"))
    swap: Decimal = Field(default=Decimal("0"))
    taxes: Decimal = Field(default=Decimal("0"))
    gross_profit: Decimal = Field(default=Decimal("0"))
    net_profit: Decimal = Field(default=Decimal("0"))
    profit_currency: str = "USD"
    status: str = Field(default="closed", max_length=20)
    magic_number: int | None = None
    strategy_name: str | None = None
    comment: str | None = None
    external_trade_id: str | None = None
    tag_ids: list[UUID] = Field(default_factory=list)
    # VM fields
    has_vm: bool = Field(default=False)
    vm_lots: Decimal = Field(default=Decimal("0"))
    vm_result: str = Field(default="WIN")
    vm_net_profit: Decimal = Field(default=Decimal("0"))
    # Frontend compatibility
    pair: str = Field(..., min_length=1, max_length=50)
    dir: str = Field(..., pattern="^(BUY|SELL)$")
    lots: Decimal = Field(..., gt=0)
    result: str = Field(default="WIN")
    pnl: Decimal = Field(default=Decimal("0"))
    date: str | None = None
    year: int | None = None
    month: int | None = None


class TradeUpdate(BaseModel):
    symbol: str | None = None
    side: str | None = Field(None, pattern="^(buy|sell)$")
    volume: Decimal | None = None
    close_time: datetime | None = None
    close_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    commission: Decimal | None = None
    swap: Decimal | None = None
    taxes: Decimal | None = None
    gross_profit: Decimal | None = None
    net_profit: Decimal | None = None
    status: str | None = None
    strategy_name: str | None = None
    comment: str | None = None
    screenshot_caption: str | None = None
    tag_ids: list[UUID] | None = None
    # VM fields
    has_vm: bool | None = None
    vm_lots: Decimal | None = None
    vm_result: str | None = None
    vm_net_profit: Decimal | None = None
    # Frontend compatibility
    pair: str | None = None
    dir: str | None = Field(None, pattern="^(BUY|SELL)$")
    lots: Decimal | None = None
    result: str | None = None
    pnl: Decimal | None = None
    date: str | None = None
    year: int | None = None
    month: int | None = None


class TradeRead(BaseModel):
    id: UUID
    workspace_id: UUID
    account_id: UUID
    symbol: str
    external_trade_id: str | None
    side: str
    volume: Decimal
    open_time: datetime
    close_time: datetime | None
    open_price: Decimal
    close_price: Decimal | None
    stop_loss: Decimal | None
    take_profit: Decimal | None
    commission: Decimal
    swap: Decimal
    taxes: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    profit_currency: str
    status: str
    magic_number: int | None
    strategy_name: str | None
    comment: str | None
    screenshot_url: str | None
    screenshot_caption: str | None
    # VM fields
    has_vm: bool
    vm_lots: Decimal
    vm_result: str
    vm_net_profit: Decimal
    # Frontend compatibility
    pnl: Decimal
    pair: str
    dir: str
    lots: Decimal
    result: str
    date: str | None
    year: int | None
    month: int | None
    created_at: datetime
    updated_at: datetime
    tags: list[TradeTagRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# --- Withdrawal ---


class WithdrawalCreate(BaseModel):
    type: str = Field(..., pattern="^(deposit|withdrawal|transfer_in|transfer_out)$")
    amount: Decimal = Field(..., gt=0)
    currency: str = "USD"
    executed_at: datetime
    method: str | None = None
    external_id: str | None = None
    note: str | None = None


class WithdrawalRead(BaseModel):
    id: UUID
    workspace_id: UUID
    account_id: UUID
    type: str
    amount: Decimal
    currency: str
    executed_at: datetime
    method: str | None
    external_id: str | None
    note: str | None
    created_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
