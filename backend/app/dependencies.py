"""
Dependências globais do FastAPI: DB, auth, workspace.
"""
from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, Workspace, WorkspaceMember

# Re-export para uso nos routers
DbSession = Annotated[Session, Depends(get_db)]

security = HTTPBearer(auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    if not credentials or credentials.credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )
    return user


def get_current_workspace(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> tuple[Workspace, WorkspaceMember]:
    """Retorna o workspace atual do token e a membership do usuário. Falha se o token não tiver ws ou o usuário não for membro."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    ws_id_str = payload.get("ws") if payload else None
    if not ws_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token sem workspace. Faça login novamente ou use refresh com workspace_id.",
        )
    try:
        workspace_id = uuid.UUID(ws_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token inválido (workspace).",
        )
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace or not workspace.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace não encontrado ou inativo.",
        )
    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este workspace.",
        )
    return workspace, membership


# Tipos anotados para uso nos routers
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentWorkspace = Annotated[tuple[Workspace, WorkspaceMember], Depends(get_current_workspace)]


def require_workspace_resource(
    resource_workspace_id: uuid.UUID,
    current_workspace: tuple[Workspace, WorkspaceMember],
) -> None:
    """
    Garante que o recurso pertence ao workspace do token.
    Use em endpoints que recebem workspace_id ou resource_id; levanta HTTP 403 se não pertencer.
    """
    workspace, _ = current_workspace
    if resource_workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recurso não pertence ao workspace atual.",
        )


async def get_current_user_from_token(token: str, db: Session) -> User:
    """
    Obtém usuário a partir de um token JWT (para uso em WebSockets).
    """
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )
    return user
