"""
Modelos: TradingAccount, AccountSnapshot.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TradingAccount(Base):
    __tablename__ = "trading_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    broker_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("broker_connections.id", ondelete="SET NULL"), nullable=True
    )
    external_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    platform: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    leverage: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    trades: Mapped[list["Trade"]] = relationship(
        "Trade", back_populates="account", cascade="all, delete-orphan"
    )
    withdrawals: Mapped[list["Withdrawal"]] = relationship(
        "Withdrawal", back_populates="account", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["AccountSnapshot"]] = relationship(
        "AccountSnapshot", back_populates="account", cascade="all, delete-orphan"
    )
    broker_connection: Mapped["BrokerConnection"] = relationship(
        "BrokerConnection", back_populates="trading_accounts"
    )


class AccountSnapshot(Base):
    __tablename__ = "account_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    equity: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    margin: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    free_margin: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)

    account: Mapped["TradingAccount"] = relationship(
        "TradingAccount", back_populates="snapshots"
    )
