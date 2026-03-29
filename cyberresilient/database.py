"""
Database engine and session management.
Uses SQLite by default; set DATABASE_URL env var for PostgreSQL.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DB_DIR = Path(__file__).resolve().parent.parent / "instance"


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DB_DIR / 'cyberresilient.db'}"


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url(), echo=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def get_session() -> Session:
    return get_session_factory()()


def init_db():
    """Create all tables. Safe to call multiple times."""
    import cyberresilient.models.db_models  # noqa: F401 — register models

    Base.metadata.create_all(bind=get_engine())


def reset_engine():
    """Reset cached engine and session factory (for testing)."""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
