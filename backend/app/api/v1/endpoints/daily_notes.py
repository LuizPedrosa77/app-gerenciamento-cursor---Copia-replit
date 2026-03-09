"""
CRUD de notas diárias. UniqueConstraint: workspace_id + user_id + date.
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import CurrentUser, CurrentWorkspace, DbSession
from app.schemas.note import DailyNoteCreate, DailyNoteRead, DailyNoteUpdate
from app.services import trade_service

router = APIRouter()


@router.get("", response_model=list[DailyNoteRead])
def list_daily_notes(
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
):
    workspace, _ = current_workspace
    return trade_service.list_daily_notes(
        db, workspace.id, current_user.id,
        start_date=start_date, end_date=end_date,
    )


@router.post("", response_model=DailyNoteRead, status_code=status.HTTP_201_CREATED)
def create_daily_note(
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
    body: DailyNoteCreate,
):
    workspace, _ = current_workspace
    existing = trade_service.get_daily_note(db, workspace.id, current_user.id, body.date)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma nota para esta data. Use PATCH para atualizar.",
        )
    return trade_service.create_daily_note(db, workspace.id, current_user.id, body)


@router.get("/by-date/{note_date}", response_model=DailyNoteRead)
def get_daily_note_by_date(
    note_date: date,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    note = trade_service.get_daily_note(db, workspace.id, current_user.id, note_date)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota não encontrada")
    return note


@router.get("/{note_id}", response_model=DailyNoteRead)
def get_daily_note(
    note_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    note = trade_service.get_daily_note_by_id(db, note_id, workspace.id)
    if not note or note.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota não encontrada")
    return note


@router.patch("/{note_id}", response_model=DailyNoteRead)
def update_daily_note(
    note_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
    body: DailyNoteUpdate,
):
    workspace, _ = current_workspace
    note = trade_service.get_daily_note_by_id(db, note_id, workspace.id)
    if not note or note.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota não encontrada")
    updated = trade_service.update_daily_note(db, note_id, workspace.id, body)
    return updated


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_daily_note(
    note_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    workspace, _ = current_workspace
    note = trade_service.get_daily_note_by_id(db, note_id, workspace.id)
    if not note or note.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota não encontrada")
    trade_service.delete_daily_note(db, note_id, workspace.id)
