"""
Upload de screenshot por trade. Armazena no MinIO e retorna URL pública.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile

from app.dependencies import CurrentUser, CurrentWorkspace, DbSession
from app.services import trade_service
from app.services import storage_service

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/{trade_id}/screenshot")
def upload_trade_screenshot(
    trade_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
    file: UploadFile = File(...),
    caption: str | None = Form(None),
):
    """Faz upload da imagem para MinIO e atualiza trade.screenshot_url e opcionalmente screenshot_caption."""
    workspace, _ = current_workspace
    trade = trade_service.get_trade(db, trade_id, workspace.id)
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade não encontrado")

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de arquivo não permitido. Use PNG, JPEG ou WEBP.",
        )
    data = file.file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo muito grande. Máximo 5MB.",
        )
    content_type = file.content_type or "image/png"
    try:
        url = storage_service.upload_screenshot(
            workspace.id, trade_id, data, content_type, file.filename
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao enviar arquivo para armazenamento: {e!s}",
        )
    trade_service.set_trade_screenshot(db, trade_id, workspace.id, url, caption=caption)
    return {"screenshot_url": url, "screenshot_caption": caption}


@router.delete("/{trade_id}/screenshot", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade_screenshot(
    trade_id: UUID,
    db: DbSession,
    current_workspace: CurrentWorkspace,
):
    """Remove a screenshot do trade e do MinIO."""
    workspace, _ = current_workspace
    trade = trade_service.get_trade(db, trade_id, workspace.id)
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade não encontrado")
    if trade.screenshot_url:
        try:
            storage_service.delete_screenshot(workspace.id, trade_id)
        except Exception:
            pass
    trade_service.set_trade_screenshot(db, trade_id, workspace.id, None, caption=None)
