"""
Schemas de autenticação: login, register, refresh, tokens.
"""
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # user_id (UUID string)
    type: str  # "access" | "refresh"
    exp: int
    ws: UUID | None = None  # workspace_id (apenas em access token)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    workspace_id: UUID | None = None  # opcional: workspace para colocar no access token


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)
    workspace_id: UUID | None = None  # opcional: workspace para o novo access token


class UserInAuth(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class WorkspaceInAuth(BaseModel):
    id: UUID
    name: str
    slug: str | None
    plan: str
    role: str  # role do usuário neste workspace

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    token: Token
    user: UserInAuth
    workspace: WorkspaceInAuth


class RegisterResponse(BaseModel):
    token: Token
    user: UserInAuth
    workspace: WorkspaceInAuth


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    user: UserInAuth
    workspace: WorkspaceInAuth
