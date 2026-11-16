-- Cyber Heist table definitions.
--
-- This file is an executable SQLite script, not a dump of a live database.
-- It describes the same tables as backend/models.py.
--
-- The FastAPI app creates tables through SQLAlchemy when you run:
--   python seed.py
-- You can also apply this script yourself:
--   sqlite3 backend/cyberheist.db < database/schema.sql
--
-- SQLite type names here are TEXT. SQLAlchemy may create DATETIME or VARCHAR
-- for the same columns. SQLite stores the values the same way either way.
-- Timestamp strings are UTC.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    topic TEXT NOT NULL,
    mission_order INTEGER NOT NULL UNIQUE,
    is_mvp INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (mission_order >= 1)
);

CREATE TABLE IF NOT EXISTS puzzles (
    id INTEGER PRIMARY KEY,
    mission_id INTEGER NOT NULL REFERENCES missions (id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    puzzle_type TEXT NOT NULL,
    instructions TEXT NOT NULL,
    solution_hash TEXT NOT NULL,
    points INTEGER NOT NULL,
    puzzle_order INTEGER NOT NULL,
    UNIQUE (mission_id, puzzle_order),
    CHECK (points >= 0),
    CHECK (puzzle_order >= 1)
);

CREATE TABLE IF NOT EXISTS puzzle_attempts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id),
    puzzle_id INTEGER NOT NULL REFERENCES puzzles (id),
    is_correct INTEGER NOT NULL,
    points_earned INTEGER NOT NULL DEFAULT 0,
    attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (points_earned >= 0),
    CHECK (is_correct = 1 OR points_earned = 0)
);

CREATE TABLE IF NOT EXISTS user_progress (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id),
    mission_id INTEGER NOT NULL REFERENCES missions (id),
    status TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE (user_id, mission_id),
    CHECK (status IN ('locked', 'available', 'in_progress', 'completed'))
);

CREATE INDEX IF NOT EXISTS idx_puzzles_mission_id ON puzzles (mission_id);
CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON puzzle_attempts (user_id);
CREATE INDEX IF NOT EXISTS idx_attempts_puzzle_id ON puzzle_attempts (puzzle_id);
CREATE INDEX IF NOT EXISTS idx_progress_user_id ON user_progress (user_id);
CREATE INDEX IF NOT EXISTS idx_progress_mission_id ON user_progress (mission_id);

CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash TEXT PRIMARY KEY NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id ON auth_sessions(user_id);
