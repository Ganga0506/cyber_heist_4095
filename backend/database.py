"""SQLite connection setup for Cyber Heist.

The development database file is backend/cyberheist.db. Tests pass
DATABASE_URL and build their own engine, so they do not write that file.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BACKEND_DIR / "cyberheist.db"

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

_engine = None


def get_database_url() -> str:
    override = os.getenv("DATABASE_URL")
    if override:
        return override
    return f"sqlite:///{DEFAULT_DB_PATH}"


def enable_sqlite_foreign_keys(engine) -> None:
    """Turn on SQLite foreign key checks for every new connection."""
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine():
    global _engine
    if _engine is None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args)
        enable_sqlite_foreign_keys(_engine)
        SessionLocal.configure(bind=_engine)
    return _engine


def get_db():
    """FastAPI dependency that opens one session per request."""
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
