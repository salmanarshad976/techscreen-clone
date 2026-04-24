"""FastAPI entrypoint for the Tech Screen replica backend."""
from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import schemas
from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db import get_db, init_db
from app.models import User
from app.solver import solve_screenshot

PLAN_LIMITS: dict[str, dict[str, int]] = {
    "basic": {"tokens": 3, "audio_seconds": 60},
    "essential": {"tokens": 150, "audio_seconds": 5400},
    "professional": {"tokens": 480, "audio_seconds": 32400},
    "expert": {"tokens": 1500, "audio_seconds": 97200},
}

app = FastAPI(title="Tech Screen API", version="0.1.0")

cors_origins = [
    o.strip()
    for o in os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if o.strip()
]
# Allow any *.devinapps.com preview URL by regex (e.g. techscreen-clone-*.devinapps.com).
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or [],
    allow_origin_regex=r"https://[A-Za-z0-9-]+\.devinapps\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/auth/register",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: schemas.RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> schemas.TokenResponse:
    existing = db.query(User).filter(User.email == payload.email.lower()).one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        plan="basic",
        tokens_remaining=PLAN_LIMITS["basic"]["tokens"],
        audio_seconds_remaining=PLAN_LIMITS["basic"]["audio_seconds"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return schemas.TokenResponse(access_token=create_access_token(user.id))


@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(
    payload: schemas.LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> schemas.TokenResponse:
    user = db.query(User).filter(User.email == payload.email.lower()).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return schemas.TokenResponse(access_token=create_access_token(user.id))


@app.get("/api/me", response_model=schemas.UserOut)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@app.get("/api/dashboard", response_model=schemas.DashboardOut)
def dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.DashboardOut:
    limits = PLAN_LIMITS.get(current_user.plan, PLAN_LIMITS["basic"])
    tokens_used = max(0, limits["tokens"] - current_user.tokens_remaining)
    audio_used = max(0, limits["audio_seconds"] - current_user.audio_seconds_remaining)
    return schemas.DashboardOut(
        user=schemas.UserOut.model_validate(current_user),
        tokens_used_this_month=tokens_used,
        audio_seconds_used_this_month=audio_used,
        plan_limits=limits,
    )


@app.post("/api/dashboard/consume-token", response_model=schemas.UserOut)
def consume_token(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if current_user.tokens_remaining <= 0:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "No tokens remaining")
    current_user.tokens_remaining -= 1
    db.commit()
    db.refresh(current_user)
    return current_user


@app.post("/api/solve", response_model=schemas.SolveResponse)
def solve(
    payload: schemas.SolveRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> schemas.SolveResponse:
    if current_user.tokens_remaining <= 0:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "No tokens remaining")

    try:
        result = solve_screenshot(payload.image_base64, payload.prompt)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    current_user.tokens_remaining -= 1
    db.commit()
    db.refresh(current_user)
    return schemas.SolveResponse(
        answer=result.answer,
        tokens_remaining=current_user.tokens_remaining,
        used_mock=result.used_mock,
    )
