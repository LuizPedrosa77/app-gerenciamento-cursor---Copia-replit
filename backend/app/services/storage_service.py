"""
Upload/download/delete de screenshots no MinIO (bucket gpfx-screenshots).
Path: {workspace_id}/{trade_id}.{ext}
Retorna URL pública (presigned ou MINIO_PUBLIC_URL).
"""
import io
import uuid
from datetime import timedelta

from minio import Minio

from app.core.config import settings
from app.core.storage import get_minio_client

BUCKET = settings.MINIO_BUCKET_SCREENSHOTS
PRESIGN_EXPIRY_DAYS = 7


def _ensure_bucket(client: Minio) -> None:
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)


def _object_name(workspace_id: uuid.UUID, trade_id: uuid.UUID, ext: str) -> str:
    return f"{workspace_id}/{trade_id}.{ext}"


def _content_type(ext: str) -> str:
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }.get(ext.lower(), "application/octet-stream")


def upload_screenshot(
    workspace_id: uuid.UUID,
    trade_id: uuid.UUID,
    data: bytes,
    content_type: str,
    filename: str | None = None,
) -> str:
    """Faz upload do arquivo, garante bucket, retorna URL pública."""
    client = get_minio_client()
    _ensure_bucket(client)
    ext = "png"
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ("png", "jpg", "jpeg", "webp"):
        ext = "png"
    object_name = _object_name(workspace_id, trade_id, ext)
    client.put_object(
        BUCKET,
        object_name,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type or _content_type(ext),
    )
    if settings.MINIO_PUBLIC_URL:
        base = settings.MINIO_PUBLIC_URL.rstrip("/")
        return f"{base}/{BUCKET}/{object_name}"
    return client.presigned_get_object(BUCKET, object_name, expires=timedelta(days=PRESIGN_EXPIRY_DAYS))


def delete_screenshot(workspace_id: uuid.UUID, trade_id: uuid.UUID, object_key: str | None = None) -> bool:
    """Remove objeto do bucket. Se object_key não for passado, tenta remover por prefix workspace_id/trade_id."""
    client = get_minio_client()
    if object_key:
        try:
            client.remove_object(BUCKET, object_key)
            return True
        except Exception:
            return False
    prefix = f"{workspace_id}/{trade_id}."
    objects = list(client.list_objects(BUCKET, prefix=prefix))
    for obj in objects:
        client.remove_object(BUCKET, obj.object_name)
    return True
