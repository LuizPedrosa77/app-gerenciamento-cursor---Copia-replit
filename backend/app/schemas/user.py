"""
Schemas de usuário e workspace (leitura, criação).
"""
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class WorkspaceRead(BaseModel):
    id: UUID
    name: str
    slug: str | None
    owner_user_id: UUID
    plan: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceReadWithRole(WorkspaceRead):
    role: str  # owner | admin | member
