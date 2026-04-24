"""Pydantic schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    plan: str
    tokens_remaining: int
    audio_seconds_remaining: int
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    user: UserOut
    tokens_used_this_month: int
    audio_seconds_used_this_month: int
    plan_limits: dict[str, int]


class SolveRequest(BaseModel):
    image_base64: str = Field(min_length=64, description="PNG/JPEG bytes, base64.")
    prompt: str | None = Field(default=None, max_length=4000)


class SolveResponse(BaseModel):
    answer: str
    tokens_remaining: int
    used_mock: bool = False
