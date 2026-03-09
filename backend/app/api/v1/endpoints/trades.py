"""
CRUD de trades por conta. Filtros: year, month, pair, direction, result, paginação.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import CurrentUser, CurrentWorkspace, DbSession
from app.schemas.trade import TradeCreate, TradeRead, TradeUpdate
from app.services import account_service
from app.services import trade_service

router = APIRouter()


@router.get("/{account_id}/trades", response_model=dict)
def list_trades(
    account_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
    year: int | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    pair: str | None = Query(None),
    direction: str | None = Query(None, pattern="^(buy|sell)$"),
    result: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    workspace, _ = current_workspace
    account = account_service.get_account(db, account_id, workspace.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    trades, total = trade_service.list_trades(
        db, workspace.id, account_id,
        year=year, month=month, pair=pair, direction=direction, result=result,
        skip=skip, limit=limit,
    )
    items = [trade_service._trade_to_read(t) for t in trades]
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/{account_id}/trades", response_model=TradeRead, status_code=status.HTTP_201_CREATED)
def create_trade(
    account_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
    body: TradeCreate,
):
    workspace, _ = current_workspace
    trade = trade_service.create_trade(db, workspace.id, account_id, body)
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    return trade_service._trade_to_read(trade)


@router.get("/{account_id}/trades/{trade_id}", response_model=TradeRead)
def get_trade(
    account_id: UUID,
    trade_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    account = account_service.get_account(db, account_id, workspace.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    trade = trade_service.get_trade(db, trade_id, workspace.id)
    if not trade or trade.account_id != account_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade não encontrado")
    return trade_service._trade_to_read(trade)


@router.patch("/{account_id}/trades/{trade_id}", response_model=TradeRead)
def update_trade(
    account_id: UUID,
    trade_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
    body: TradeUpdate,
):
    workspace, _ = current_workspace
    account = account_service.get_account(db, account_id, workspace.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    trade = trade_service.update_trade(db, trade_id, workspace.id, body)
    if not trade or trade.account_id != account_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade não encontrado")
    return trade_service._trade_to_read(trade)


@router.delete("/{account_id}/trades/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade(
    account_id: UUID,
    trade_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    account = account_service.get_account(db, account_id, workspace.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada")
    trade = trade_service.get_trade(db, trade_id, workspace.id)
    if not trade or trade.account_id != account_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade não encontrado")
    trade_service.delete_trade(db, trade_id, workspace.id)
