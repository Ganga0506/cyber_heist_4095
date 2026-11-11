"""Pytest fixtures that use a temporary SQLite file, never cyberheist.db."""

import os

# Set this before importing the app so TestClient does not create the dev database.
os.environ["CYBERHEIST_AUTO_CREATE"] = "0"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from seed import seed
from tests.db_utils import make_engine


@pytest.fixture
def seeded_session(tmp_path):
    engine = make_engine(tmp_path / "test.db")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    seed(session)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(seeded_session):
    engine = seeded_session.get_bind()
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
