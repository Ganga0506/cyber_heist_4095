"""Shared helpers for tests. Kept out of conftest so imports stay simple."""

from pathlib import Path

from sqlalchemy import create_engine

from database import enable_sqlite_foreign_keys


def make_engine(path: Path):
    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )
    enable_sqlite_foreign_keys(engine)
    return engine
