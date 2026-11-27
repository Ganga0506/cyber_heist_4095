"""Database creation, demo records, and constraints."""

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database import Base
from models import Mission, Puzzle, PuzzleAttempt, User, UserProgress
from security import hash_solution, verify_password
from seed import (
    DEMO_PUZZLES,
    DEMO_USERS,
    init_db,
    render_seed_sql,
    seed,
)
from tests.db_utils import make_engine

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = ROOT / "database" / "schema.sql"
SEED_SQL = ROOT / "database" / "seed.sql"

EXPECTED_MISSIONS = [
    ("THE SETUP", True),
    ("THE PERIMETER", True),
    ("THE ENCRYPTION LAYER", False),
    ("INSIDE THE SYSTEM", False),
    ("THE FINAL HEIST", True),
]

EXPECTED_COUNTS = {
    "users": 5,
    "missions": 5,
    "puzzles": 10,
    "puzzle_attempts": 16,
    "user_progress": 25,
}


def _counts(session):
    return {
        "users": session.query(User).count(),
        "missions": session.query(Mission).count(),
        "puzzles": session.query(Puzzle).count(),
        "puzzle_attempts": session.query(PuzzleAttempt).count(),
        "user_progress": session.query(UserProgress).count(),
    }


def test_database_creation(tmp_path):
    engine = make_engine(tmp_path / "empty.db")
    Base.metadata.create_all(bind=engine)
    names = set(inspect(engine).get_table_names())
    assert names == {
        "auth_sessions",
        "account_mfa",
        "google_flows",
        "google_handoffs",
        "google_identities",
        "password_resets",
        "users",
        "missions",
        "puzzles",
        "puzzle_attempts",
        "lesson_drafts",
        "hint_purchases",
        "user_progress",
    }
    engine.dispose()


def test_seed_counts(seeded_session):
    assert _counts(seeded_session) == EXPECTED_COUNTS


def test_missions_are_in_order(seeded_session):
    rows = (
        seeded_session.query(Mission)
        .order_by(Mission.mission_order)
        .all()
    )
    assert [(row.title, bool(row.is_mvp)) for row in rows] == EXPECTED_MISSIONS
    assert [row.mission_order for row in rows] == [1, 2, 3, 4, 5]


def test_each_mission_has_at_least_two_puzzles(seeded_session):
    missions = seeded_session.query(Mission).all()
    assert len(missions) == 5
    for mission in missions:
        puzzle_count = (
            seeded_session.query(Puzzle).filter_by(mission_id=mission.id).count()
        )
        assert puzzle_count >= 2


def test_foreign_keys_are_enforced(seeded_session):
    with pytest.raises(IntegrityError):
        seeded_session.execute(
            text(
                "INSERT INTO puzzles "
                "(mission_id, title, description, puzzle_type, instructions, "
                "solution_hash, points, puzzle_order) "
                "VALUES (999, 'x', 'x', 'demo', 'x', 'abc', 1, 1)"
            )
        )
        seeded_session.commit()
    seeded_session.rollback()

    with pytest.raises(IntegrityError):
        seeded_session.execute(
            text(
                "INSERT INTO puzzle_attempts "
                "(user_id, puzzle_id, is_correct, points_earned, attempted_at) "
                "VALUES (999, 1, 0, 0, '2026-04-01 00:00:00')"
            )
        )
        seeded_session.commit()
    seeded_session.rollback()

    with pytest.raises(IntegrityError):
        seeded_session.execute(
            text(
                "INSERT INTO user_progress (user_id, mission_id, status) "
                "VALUES (1, 999, 'locked')"
            )
        )
        seeded_session.commit()
    seeded_session.rollback()


def test_username_and_email_must_be_unique(seeded_session):
    seeded_session.add(
        User(
            username="nova.agent",
            email="someone.else@example.com",
            password_hash="not-a-real-hash",
        )
    )
    with pytest.raises(IntegrityError):
        seeded_session.commit()
    seeded_session.rollback()

    seeded_session.add(
        User(
            username="new.agent",
            email="nova.agent@example.com",
            password_hash="not-a-real-hash",
        )
    )
    with pytest.raises(IntegrityError):
        seeded_session.commit()
    seeded_session.rollback()


def test_progress_status_is_constrained(seeded_session):
    with pytest.raises(IntegrityError):
        seeded_session.execute(
            text(
                "UPDATE user_progress SET status = 'unlocked' "
                "WHERE user_id = 1 AND mission_id = 1"
            )
        )
        seeded_session.commit()
    seeded_session.rollback()


def test_seed_is_idempotent(seeded_session):
    before = _counts(seeded_session)
    seed(seeded_session)
    seed(seeded_session)
    assert _counts(seeded_session) == before


def test_demo_passwords_match_hashes_and_are_not_stored_plaintext(seeded_session):
    for row in DEMO_USERS:
        user = seeded_session.query(User).filter_by(username=row["username"]).one()
        assert verify_password(row["password"], user.password_hash)
        assert row["password"] not in user.password_hash
        assert "password_hash" not in row["password"]


def test_puzzle_answers_are_stored_as_hashes(seeded_session):
    for row in DEMO_PUZZLES:
        puzzle = seeded_session.query(Puzzle).filter_by(title=row["title"]).one()
        assert puzzle.solution_hash == hash_solution(row["answer"])
        assert puzzle.solution_hash != row["answer"]
        assert len(puzzle.solution_hash) == 64


def test_schema_sql_matches_model_columns(tmp_path):
    engine = make_engine(tmp_path / "orm.db")
    Base.metadata.create_all(bind=engine)
    orm_columns = {
        table.name: [column.name for column in table.columns]
        for table in Base.metadata.sorted_tables
    }
    engine.dispose()

    sql_path = tmp_path / "sql.db"
    connection = sqlite3.connect(sql_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
    sql_columns = {}
    foreign_keys = {}
    for table in orm_columns:
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
        sql_columns[table] = [row[1] for row in rows]
        foreign_keys[table] = connection.execute(
            f"PRAGMA foreign_key_list({table})"
        ).fetchall()
    connection.close()

    assert sql_columns == orm_columns
    orm_targets = {
        table: {fk.column.table.name for fk in Base.metadata.tables[table].foreign_keys}
        for table in ("puzzles", "puzzle_attempts", "user_progress")
    }
    assert orm_targets["puzzles"] == {"missions"}
    assert orm_targets["puzzle_attempts"] == {"users", "puzzles"}
    assert orm_targets["user_progress"] == {"users", "missions"}

    puzzle_fks = {row[0] for row in _fk_targets(foreign_keys["puzzles"])}
    assert puzzle_fks == {"missions"}
    attempt_fks = {item[0] for item in _fk_targets(foreign_keys["puzzle_attempts"])}
    assert attempt_fks == {"users", "puzzles"}
    progress_fks = {item[0] for item in _fk_targets(foreign_keys["user_progress"])}
    assert progress_fks == {"users", "missions"}


def _fk_targets(rows):
    # PRAGMA foreign_key_list: id, seq, table, from, to, ...
    return [(row[2], row[3], row[4]) for row in rows]


def test_seed_sql_matches_python_and_loads(tmp_path):
    assert SEED_SQL.read_text(encoding="utf-8") == render_seed_sql()

    sql_path = tmp_path / "from_sql.db"
    connection = sqlite3.connect(sql_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
    connection.executescript(SEED_SQL.read_text(encoding="utf-8"))
    # A second run must not create extra rows.
    connection.executescript(SEED_SQL.read_text(encoding="utf-8"))

    engine = make_engine(tmp_path / "from_python.db")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    seed(session)

    sql_counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in EXPECTED_COUNTS
    }
    assert sql_counts == EXPECTED_COUNTS
    assert _counts(session) == sql_counts

    sql_missions = connection.execute(
        "SELECT title, is_mvp FROM missions ORDER BY mission_order"
    ).fetchall()
    py_missions = (
        session.query(Mission.title, Mission.is_mvp)
        .order_by(Mission.mission_order)
        .all()
    )
    assert [(row["title"], row["is_mvp"]) for row in sql_missions] == [
        (title, int(is_mvp)) for title, is_mvp in py_missions
    ]

    sql_hashes = connection.execute(
        "SELECT title, solution_hash FROM puzzles ORDER BY id"
    ).fetchall()
    py_hashes = (
        session.query(Puzzle.title, Puzzle.solution_hash).order_by(Puzzle.id).all()
    )
    assert [(row["title"], row["solution_hash"]) for row in sql_hashes] == list(py_hashes)

    session.close()
    engine.dispose()
    connection.close()


def test_incorrect_attempt_cannot_award_points(seeded_session):
    with pytest.raises(IntegrityError):
        seeded_session.execute(
            text(
                "INSERT INTO puzzle_attempts "
                "(user_id, puzzle_id, is_correct, points_earned, attempted_at) "
                "VALUES (3, 1, 0, 50, '2026-04-02 00:00:00')"
            )
        )
        seeded_session.commit()
    seeded_session.rollback()


def test_init_db_creates_tables_without_rows(tmp_path, monkeypatch):
    import database

    db_path = tmp_path / "init-only.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    previous_engine = database._engine
    database._engine = None
    try:
        init_db()
        engine = database.get_engine()
        session = sessionmaker(bind=engine)()
        assert set(inspect(engine).get_table_names()) >= set(EXPECTED_COUNTS)
        assert session.query(User).count() == 0
        session.close()
    finally:
        if database._engine is not None:
            database._engine.dispose()
        database._engine = previous_engine
