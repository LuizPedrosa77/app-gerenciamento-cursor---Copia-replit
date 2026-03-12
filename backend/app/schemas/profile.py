from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    trading_style: Optional[str] = None
    experience_level: Optional[str] = None


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    cpf: Optional[str]
    phone: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    trading_style: Optional[str]
    experience_level: Optional[str]
    plan: str
    has_google: bool
    created_at: datetime


class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    notifications_email: Optional[bool] = None
    notifications_push: Optional[bool] = None


class PreferencesResponse(BaseModel):
    theme: str = "dark"
    language: str = "pt-BR"
    currency: str = "USD"
    timezone: str = "America/Sao_Paulo"
    notifications_email: bool = True
    notifications_push: bool = True
