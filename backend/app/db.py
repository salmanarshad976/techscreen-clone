"""Database setup using SQLAlchemy 2.x."""
from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

def _default_database_url() -> str:
    # Prefer Fly.io persistent volume when present.
    if os.path.isdir("/data"):
        return "sqlite:////data/techscreen.db"
    return "sqlite:///./techscreen.db"


DATABASE_URL = os.environ.get("DATABASE_URL", _default_database_url())

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)
