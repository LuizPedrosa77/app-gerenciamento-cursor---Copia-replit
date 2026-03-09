"""
CRUD de saques/depósitos por conta.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import CurrentUser, CurrentWorkspace, DbSession
from app.schemas.trade import WithdrawalCreate, WithdrawalRead
from app.services import account_service
from app.services import trade_service

router = APIRouter()


@router.get("/{account_id}/withdrawals", response_model=list[WithdrawalRead])
def list_withdrawals(
    account_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    account = account_service.get_account(db, account_id, workspace.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    return trade_service.list_withdrawals(db, workspace.id, account_id)


@router.post("/{account_id}/withdrawals", response_model=WithdrawalRead, status_code=status.HTTP_201_CREATED)
def create_withdrawal(
    account_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
    body: WithdrawalCreate,
):
    workspace, _ = current_workspace
    w = trade_service.create_withdrawal(
        db, workspace.id, account_id, current_user.id, body
    )
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    return w


@router.delete("/{account_id}/withdrawals/{withdrawal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_withdrawal(
    account_id: UUID,
    withdrawal_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    account = account_service.get_account(db, account_id, workspace.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    w = trade_service.get_withdrawal(db, withdrawal_id, workspace.id)
    if not w or w.account_id != account_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saque não encontrado")
    trade_service.delete_withdrawal(db, withdrawal_id, workspace.id)
