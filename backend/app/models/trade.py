"""
Modelos: Trade, TradeTag, TradeTagLink, Withdrawal.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    external_trade_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # buy, sell
    volume: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    open_price: Mapped[Decimal] = mapped_column(Numeric(20, 5), nullable=False)
    close_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 5), nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(20, 5), nullable=True)
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(20, 5), nullable=True)
    commission: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    swap: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    taxes: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    net_profit: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    profit_currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="closed", nullable=False)
    magic_number: Mapped[int | None] = mapped_column(nullable=True)
    strategy_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    screenshot_caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    account: Mapped["TradingAccount"] = relationship(
        "TradingAccount", back_populates="trades"
    )
    tag_links: Mapped[list["TradeTagLink"]] = relationship(
        "TradeTagLink", back_populates="trade", cascade="all, delete-orphan"
    )


class TradeTag(Base):
    __tablename__ = "trade_tags"
    __table_args__ = (UniqueConstraint("workspace_id", "name", name="uq_workspace_tag_name"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)

    tag_links: Mapped[list["TradeTagLink"]] = relationship(
        "TradeTagLink", back_populates="tag", cascade="all, delete-orphan"
    )


class TradeTagLink(Base):
    __tablename__ = "trade_tag_links"
    __table_args__ = (UniqueConstraint("trade_id", "tag_id", name="uq_trade_tag"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trades.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trade_tags.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    trade: Mapped["Trade"] = relationship("Trade", back_populates="tag_links")
    tag: Mapped["TradeTag"] = relationship("TradeTag", back_populates="tag_links")


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)  # deposit, withdrawal, etc.
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    account: Mapped["TradingAccount"] = relationship(
        "TradingAccount", back_populates="withdrawals"
    )
