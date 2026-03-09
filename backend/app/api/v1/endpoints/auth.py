"""
Endpoints de autenticação: register, login, refresh, me.
"""
from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, CurrentWorkspace, DbSession
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshRequest,
    RefreshResponse,
    MeResponse,
    UserInAuth,
    WorkspaceInAuth,
)
from app.services.auth_service import register as do_register, login as do_login, refresh_tokens

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
def register(db: DbSession, body: RegisterRequest):
    try:
        return do_register(db, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginResponse)
def login(db: DbSession, body: LoginRequest):
    try:
        return do_login(db, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=RefreshResponse)
def refresh(db: DbSession, body: RefreshRequest):
    try:
        return refresh_tokens(db, body.refresh_token, body.workspace_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=MeResponse)
def me(
    current_user: CurrentUser,
    current_workspace: CurrentWorkspace,
):
    workspace, membership = current_workspace
    return MeResponse(
        user=UserInAuth(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            is_active=current_user.is_active,
        ),
        workspace=WorkspaceInAuth(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            plan=workspace.plan,
            role=membership.role,
        ),
    )
