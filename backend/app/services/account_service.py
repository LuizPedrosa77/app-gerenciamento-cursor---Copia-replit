"""
CRUD de contas de trading (sempre filtrado por workspace_id).
"""
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import TradingAccount
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate


def list_accounts(db: Session, workspace_id: uuid.UUID) -> list[TradingAccount]:
    return (
        db.query(TradingAccount)
        .filter(TradingAccount.workspace_id == workspace_id)
        .order_by(TradingAccount.created_at.desc())
        .all()
    )


def get_account(
    db: Session, account_id: uuid.UUID, workspace_id: uuid.UUID
) -> TradingAccount | None:
    return (
        db.query(TradingAccount)
        .filter(
            TradingAccount.id == account_id,
            TradingAccount.workspace_id == workspace_id,
        )
        .first()
    )


def create_account(
    db: Session, workspace_id: uuid.UUID, data: AccountCreate
) -> TradingAccount:
    balance = data.current_balance if data.current_balance is not None else data.initial_balance
    account = TradingAccount(
        workspace_id=workspace_id,
        name=data.name,
        currency=data.currency,
        platform=data.platform,
        is_demo=data.is_demo,
        initial_balance=data.initial_balance,
        current_balance=balance,
        leverage=data.leverage,
        external_account_id=data.external_account_id,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_account(
    db: Session, account_id: uuid.UUID, workspace_id: uuid.UUID, data: AccountUpdate
) -> TradingAccount | None:
    account = get_account(db, account_id, workspace_id)
    if not account:
        return None
    update = data.model_dump(exclude_unset=True)
    for k, v in update.items():
        setattr(account, k, v)
    db.commit()
    db.refresh(account)
    return account


def delete_account(
    db: Session, account_id: uuid.UUID, workspace_id: uuid.UUID
) -> bool:
    account = get_account(db, account_id, workspace_id)
    if not account:
        return False
    db.delete(account)
    db.commit()
    return True
