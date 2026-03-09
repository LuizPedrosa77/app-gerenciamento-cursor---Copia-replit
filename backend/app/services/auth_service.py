"""
Serviço de autenticação: registro, login, refresh.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User, Workspace, WorkspaceMember
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshResponse,
    UserInAuth,
    WorkspaceInAuth,
    Token,
)


def _user_to_auth(user: User) -> UserInAuth:
    return UserInAuth(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
    )


def _workspace_with_role(workspace: Workspace, role: str) -> WorkspaceInAuth:
    return WorkspaceInAuth(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        plan=workspace.plan,
        role=role,
    )


def _get_first_workspace_for_user(db: Session, user_id: uuid.UUID) -> tuple[Workspace, str] | None:
    membership = (
        db.query(WorkspaceMember)
        .join(Workspace)
        .filter(
            WorkspaceMember.user_id == user_id,
            Workspace.is_active.is_(True),
        )
        .order_by(WorkspaceMember.created_at)
        .first()
    )
    if not membership:
        return None
    return membership.workspace, membership.role


def register(db: Session, data: RegisterRequest) -> RegisterResponse:
    if db.query(User).filter(User.email == data.email).first():
        raise ValueError("Email já cadastrado")

    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()

    workspace = Workspace(
        name="Meu Workspace",
        owner_user_id=user.id,
        plan="free",
        is_active=True,
    )
    db.add(workspace)
    db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner",
    )
    db.add(member)
    db.commit()
    db.refresh(user)
    db.refresh(workspace)

    access = create_access_token(str(user.id), workspace_id=str(workspace.id))
    refresh = create_refresh_token(str(user.id))

    return RegisterResponse(
        token=Token(access_token=access, refresh_token=refresh),
        user=_user_to_auth(user),
        workspace=_workspace_with_role(workspace, "owner"),
    )


def login(db: Session, data: LoginRequest) -> LoginResponse:
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise ValueError("Email ou senha inválidos")
    if not user.is_active:
        raise ValueError("Usuário inativo")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    workspace: Workspace | None = None
    role = "member"

    if data.workspace_id:
        membership = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.user_id == user.id,
                WorkspaceMember.workspace_id == data.workspace_id,
            )
            .first()
        )
        if membership:
            workspace = membership.workspace
            role = membership.role
    if workspace is None:
        first = _get_first_workspace_for_user(db, user.id)
        if first:
            workspace, role = first

    if not workspace:
        raise ValueError("Nenhum workspace encontrado para este usuário")

    access = create_access_token(str(user.id), workspace_id=str(workspace.id))
    refresh = create_refresh_token(str(user.id))

    return LoginResponse(
        token=Token(access_token=access, refresh_token=refresh),
        user=_user_to_auth(user),
        workspace=_workspace_with_role(workspace, role),
    )


def refresh_tokens(db: Session, refresh_token: str, workspace_id: uuid.UUID | None) -> RefreshResponse:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise ValueError("Refresh token inválido ou expirado")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise ValueError("Refresh token inválido")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise ValueError("Refresh token inválido")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise ValueError("Usuário não encontrado ou inativo")

    workspace: Workspace | None = None
    if workspace_id:
        membership = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.user_id == user.id,
                WorkspaceMember.workspace_id == workspace_id,
            )
            .first()
        )
        if membership:
            workspace = membership.workspace
    if workspace is None:
        first = _get_first_workspace_for_user(db, user.id)
        if first:
            workspace, _ = first

    ws_id = str(workspace.id) if workspace else None
    access = create_access_token(str(user.id), workspace_id=ws_id)
    return RefreshResponse(access_token=access)
