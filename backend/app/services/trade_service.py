"""
CRUD de trades, tags, saques e notas diárias (sempre filtrado por workspace_id).
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import extract
from sqlalchemy.orm import Session, joinedload

from app.models.account import TradingAccount
from app.models.trade import Trade, TradeTag, TradeTagLink, Withdrawal
from app.models.note import DailyNote
from app.schemas.trade import TradeCreate, TradeUpdate, TradeRead, TradeTagRead, WithdrawalCreate, WithdrawalRead
from app.schemas.note import DailyNoteCreate, DailyNoteUpdate, DailyNoteRead
from app.services.account_service import get_account as get_trading_account


# --- Trades ---


def _trade_to_read(trade: Trade) -> TradeRead:
    tags = [TradeTagRead.model_validate(link.tag) for link in trade.tag_links]
    return TradeRead(
        id=trade.id,
        workspace_id=trade.workspace_id,
        account_id=trade.account_id,
        symbol=trade.symbol,
        external_trade_id=trade.external_trade_id,
        side=trade.side,
        volume=trade.volume,
        open_time=trade.open_time,
        close_time=trade.close_time,
        open_price=trade.open_price,
        close_price=trade.close_price,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        commission=trade.commission,
        swap=trade.swap,
        taxes=trade.taxes,
        gross_profit=trade.gross_profit,
        net_profit=trade.net_profit,
        profit_currency=trade.profit_currency,
        status=trade.status,
        magic_number=trade.magic_number,
        strategy_name=trade.strategy_name,
        comment=trade.comment,
        screenshot_url=trade.screenshot_url,
        screenshot_caption=trade.screenshot_caption,
        created_at=trade.created_at,
        updated_at=trade.updated_at,
        tags=tags,
    )


def list_trades(
    db: Session,
    workspace_id: uuid.UUID,
    account_id: uuid.UUID,
    *,
    year: int | None = None,
    month: int | None = None,
    pair: str | None = None,
    direction: str | None = None,  # buy / sell
    result: str | None = None,     # status ou net_profit > 0
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Trade], int]:
    account = get_trading_account(db, account_id, workspace_id)
    if not account:
        return [], 0
    q = (
        db.query(Trade)
        .filter(Trade.workspace_id == workspace_id, Trade.account_id == account_id)
        .options(joinedload(Trade.tag_links).joinedload(TradeTagLink.tag))
    )
    if year is not None:
        q = q.filter(extract("year", Trade.open_time) == year)
    if month is not None:
        q = q.filter(extract("month", Trade.open_time) == month)
    if pair:
        q = q.filter(Trade.symbol.ilike(f"%{pair}%"))
    if direction:
        q = q.filter(Trade.side == direction.lower())
    if result:
        r = result.lower()
        if r in ("win", "loss"):
            if r == "win":
                q = q.filter(Trade.net_profit > 0)
            else:
                q = q.filter(Trade.net_profit <= 0)
        else:
            q = q.filter(Trade.status == result)
    total = q.count()
    trades = q.order_by(Trade.open_time.desc()).offset(skip).limit(limit).all()
    return trades, total


def get_trade(
    db: Session, trade_id: uuid.UUID, workspace_id: uuid.UUID
) -> Trade | None:
    return (
        db.query(Trade)
        .filter(Trade.id == trade_id, Trade.workspace_id == workspace_id)
        .options(joinedload(Trade.tag_links).joinedload(TradeTagLink.tag))
        .first()
    )


def _sync_trade_tags(db: Session, trade: Trade, tag_ids: list[uuid.UUID], workspace_id: uuid.UUID) -> None:
    # Remove links cujo tag não está em tag_ids; adiciona novos
    existing = {link.tag_id for link in trade.tag_links}
    to_add = set(tag_ids) - existing
    to_remove = existing - set(tag_ids)
    for link in trade.tag_links:
        if link.tag_id in to_remove:
            db.delete(link)
    # Validar que tags pertencem ao workspace
    if to_add:
        tags = db.query(TradeTag).filter(
            TradeTag.id.in_(to_add),
            TradeTag.workspace_id == workspace_id,
        ).all()
        valid_ids = {t.id for t in tags}
        for tid in to_add:
            if tid in valid_ids:
                db.add(TradeTagLink(trade_id=trade.id, tag_id=tid))
    db.flush()


def create_trade(
    db: Session, workspace_id: uuid.UUID, account_id: uuid.UUID, data: TradeCreate
) -> Trade | None:
    account = get_trading_account(db, account_id, workspace_id)
    if not account:
        return None
    trade = Trade(
        workspace_id=workspace_id,
        account_id=account_id,
        symbol=data.symbol,
        external_trade_id=data.external_trade_id,
        side=data.side,
        volume=data.volume,
        open_time=data.open_time,
        close_time=data.close_time,
        open_price=data.open_price,
        close_price=data.close_price,
        stop_loss=data.stop_loss,
        take_profit=data.take_profit,
        commission=data.commission,
        swap=data.swap,
        taxes=data.taxes,
        gross_profit=data.gross_profit,
        net_profit=data.net_profit,
        profit_currency=data.profit_currency,
        status=data.status,
        magic_number=data.magic_number,
        strategy_name=data.strategy_name,
        comment=data.comment,
    )
    db.add(trade)
    db.flush()
    if data.tag_ids:
        _sync_trade_tags(db, trade, data.tag_ids, workspace_id)
    db.commit()
    db.refresh(trade)
    db.refresh(trade)  # load tag_links
    trade = get_trade(db, trade.id, workspace_id)
    return trade


def update_trade(
    db: Session, trade_id: uuid.UUID, workspace_id: uuid.UUID, data: TradeUpdate
) -> Trade | None:
    trade = get_trade(db, trade_id, workspace_id)
    if not trade:
        return None
    update = data.model_dump(exclude_unset=True)
    tag_ids = update.pop("tag_ids", None)
    for k, v in update.items():
        setattr(trade, k, v)
    if tag_ids is not None:
        _sync_trade_tags(db, trade, tag_ids, workspace_id)
    db.commit()
    db.refresh(trade)
    return get_trade(db, trade_id, workspace_id)


def delete_trade(db: Session, trade_id: uuid.UUID, workspace_id: uuid.UUID) -> bool:
    trade = get_trade(db, trade_id, workspace_id)
    if not trade:
        return False
    db.delete(trade)
    db.commit()
    return True


def set_trade_screenshot(
    db: Session, trade_id: uuid.UUID, workspace_id: uuid.UUID, url: str | None, caption: str | None = None
) -> Trade | None:
    trade = get_trade(db, trade_id, workspace_id)
    if not trade:
        return None
    trade.screenshot_url = url
    if caption is not None:
        trade.screenshot_caption = caption
    db.commit()
    db.refresh(trade)
    return trade


# --- Withdrawals ---


def list_withdrawals(
    db: Session, workspace_id: uuid.UUID, account_id: uuid.UUID
) -> list[Withdrawal]:
    account = get_trading_account(db, account_id, workspace_id)
    if not account:
        return []
    return (
        db.query(Withdrawal)
        .filter(
            Withdrawal.workspace_id == workspace_id,
            Withdrawal.account_id == account_id,
        )
        .order_by(Withdrawal.executed_at.desc())
        .all()
    )


def create_withdrawal(
    db: Session,
    workspace_id: uuid.UUID,
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    data: WithdrawalCreate,
) -> Withdrawal | None:
    account = get_trading_account(db, account_id, workspace_id)
    if not account:
        return None
    w = Withdrawal(
        workspace_id=workspace_id,
        account_id=account_id,
        created_by_user_id=user_id,
        type=data.type,
        amount=data.amount,
        currency=data.currency,
        executed_at=data.executed_at,
        method=data.method,
        external_id=data.external_id,
        note=data.note,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def get_withdrawal(
    db: Session, withdrawal_id: uuid.UUID, workspace_id: uuid.UUID
) -> Withdrawal | None:
    return (
        db.query(Withdrawal)
        .filter(
            Withdrawal.id == withdrawal_id,
            Withdrawal.workspace_id == workspace_id,
        )
        .first()
    )


def delete_withdrawal(
    db: Session, withdrawal_id: uuid.UUID, workspace_id: uuid.UUID
) -> bool:
    w = get_withdrawal(db, withdrawal_id, workspace_id)
    if not w:
        return False
    db.delete(w)
    db.commit()
    return True


# --- Daily notes ---


def list_daily_notes(
    db: Session, workspace_id: uuid.UUID, user_id: uuid.UUID, start_date: date | None = None, end_date: date | None = None
) -> list[DailyNote]:
    q = db.query(DailyNote).filter(
        DailyNote.workspace_id == workspace_id,
        DailyNote.user_id == user_id,
    )
    if start_date:
        q = q.filter(DailyNote.date >= start_date)
    if end_date:
        q = q.filter(DailyNote.date <= end_date)
    return q.order_by(DailyNote.date.desc()).all()


def get_daily_note(
    db: Session, workspace_id: uuid.UUID, user_id: uuid.UUID, note_date: date
) -> DailyNote | None:
    return (
        db.query(DailyNote)
        .filter(
            DailyNote.workspace_id == workspace_id,
            DailyNote.user_id == user_id,
            DailyNote.date == note_date,
        )
        .first()
    )


def get_daily_note_by_id(
    db: Session, note_id: uuid.UUID, workspace_id: uuid.UUID
) -> DailyNote | None:
    return (
        db.query(DailyNote)
        .filter(
            DailyNote.id == note_id,
            DailyNote.workspace_id == workspace_id,
        )
        .first()
    )


def create_daily_note(
    db: Session, workspace_id: uuid.UUID, user_id: uuid.UUID, data: DailyNoteCreate
) -> DailyNote:
    note = DailyNote(
        workspace_id=workspace_id,
        user_id=user_id,
        account_id=data.account_id,
        date=data.date,
        title=data.title,
        content=data.content,
        mood=data.mood,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_daily_note(
    db: Session, note_id: uuid.UUID, workspace_id: uuid.UUID, data: DailyNoteUpdate
) -> DailyNote | None:
    note = get_daily_note_by_id(db, note_id, workspace_id)
    if not note:
        return None
    update = data.model_dump(exclude_unset=True)
    for k, v in update.items():
        setattr(note, k, v)
    db.commit()
    db.refresh(note)
    return note


def delete_daily_note(
    db: Session, note_id: uuid.UUID, workspace_id: uuid.UUID
) -> bool:
    note = get_daily_note_by_id(db, note_id, workspace_id)
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True
