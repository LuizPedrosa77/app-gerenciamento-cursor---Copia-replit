"""
CRUD de contas de trading. Sempre filtrado por workspace.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import CurrentUser, CurrentWorkspace, DbSession
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.services import account_service

router = APIRouter()


@router.get("", response_model=list[AccountRead])
def list_accounts(
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    return account_service.list_accounts(db, workspace.id)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    db: DbSession,
    current_workspace: CurrentWorkspace,
    body: AccountCreate,
):
    workspace, _ = current_workspace
    return account_service.create_account(db, workspace.id, body)


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    account = account_service.get_account(db, account_id, workspace.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    return account


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
    body: AccountUpdate,
):
    workspace, _ = current_workspace
    account = account_service.update_account(db, account_id, workspace.id, body)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    if not account_service.delete_account(db, account_id, workspace.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
