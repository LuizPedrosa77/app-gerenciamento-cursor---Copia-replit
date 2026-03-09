"""add trading_accounts trades withdrawals daily_notes

Revision ID: 002
Revises: 001
Create Date: 2025-03-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trading_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("broker_connection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_account_id", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("platform", sa.String(length=30), nullable=False, server_default="manual"),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("initial_balance", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("current_balance", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("leverage", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trading_accounts_workspace_id"), "trading_accounts", ["workspace_id"], unique=False)

    op.create_table(
        "account_snapshots",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("balance", sa.Numeric(20, 2), nullable=False),
        sa.Column("equity", sa.Numeric(20, 2), nullable=True),
        sa.Column("margin", sa.Numeric(20, 2), nullable=True),
        sa.Column("free_margin", sa.Numeric(20, 2), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["trading_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_account_snapshots_account_id"), "account_snapshots", ["account_id"], unique=False)

    op.create_table(
        "trades",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("external_trade_id", sa.String(length=100), nullable=True),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("volume", sa.Numeric(20, 4), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("open_price", sa.Numeric(20, 5), nullable=False),
        sa.Column("close_price", sa.Numeric(20, 5), nullable=True),
        sa.Column("stop_loss", sa.Numeric(20, 5), nullable=True),
        sa.Column("take_profit", sa.Numeric(20, 5), nullable=True),
        sa.Column("commission", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("swap", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("taxes", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("gross_profit", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("net_profit", sa.Numeric(20, 2), nullable=False, server_default="0"),
        sa.Column("profit_currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="closed"),
        sa.Column("magic_number", sa.Integer(), nullable=True),
        sa.Column("strategy_name", sa.String(length=100), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("screenshot_url", sa.String(length=1024), nullable=True),
        sa.Column("screenshot_caption", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["account_id"], ["trading_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trades_account_id"), "trades", ["account_id"], unique=False)
    op.create_index(op.f("ix_trades_workspace_id"), "trades", ["workspace_id"], unique=False)

    op.create_table(
        "trade_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "name", name="uq_workspace_tag_name"),
    )
    op.create_index(op.f("ix_trade_tags_workspace_id"), "trade_tags", ["workspace_id"], unique=False)

    op.create_table(
        "trade_tag_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trade_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["trade_tags.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trade_id"], ["trades.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trade_id", "tag_id", name="uq_trade_tag"),
    )
    op.create_index(op.f("ix_trade_tag_links_tag_id"), "trade_tag_links", ["tag_id"], unique=False)
    op.create_index(op.f("ix_trade_tag_links_trade_id"), "trade_tag_links", ["trade_id"], unique=False)

    op.create_table(
        "withdrawals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(length=50), nullable=True),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["account_id"], ["trading_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_withdrawals_account_id"), "withdrawals", ["account_id"], unique=False)
    op.create_index(op.f("ix_withdrawals_workspace_id"), "withdrawals", ["workspace_id"], unique=False)

    op.create_table(
        "daily_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("mood", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["account_id"], ["trading_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "user_id", "date", name="uq_daily_note_workspace_user_date"),
    )
    op.create_index(op.f("ix_daily_notes_user_id"), "daily_notes", ["user_id"], unique=False)
    op.create_index(op.f("ix_daily_notes_workspace_id"), "daily_notes", ["workspace_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_daily_notes_workspace_id"), table_name="daily_notes")
    op.drop_index(op.f("ix_daily_notes_user_id"), table_name="daily_notes")
    op.drop_table("daily_notes")
    op.drop_index(op.f("ix_withdrawals_workspace_id"), table_name="withdrawals")
    op.drop_index(op.f("ix_withdrawals_account_id"), table_name="withdrawals")
    op.drop_table("withdrawals")
    op.drop_index(op.f("ix_trade_tag_links_trade_id"), table_name="trade_tag_links")
    op.drop_index(op.f("ix_trade_tag_links_tag_id"), table_name="trade_tag_links")
    op.drop_table("trade_tag_links")
    op.drop_index(op.f("ix_trade_tags_workspace_id"), table_name="trade_tags")
    op.drop_table("trade_tags")
    op.drop_index(op.f("ix_trades_workspace_id"), table_name="trades")
    op.drop_index(op.f("ix_trades_account_id"), table_name="trades")
    op.drop_table("trades")
    op.drop_index(op.f("ix_account_snapshots_account_id"), table_name="account_snapshots")
    op.drop_table("account_snapshots")
    op.drop_index(op.f("ix_trading_accounts_workspace_id"), table_name="trading_accounts")
    op.drop_table("trading_accounts")
