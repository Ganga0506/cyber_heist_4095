"""SQLAlchemy models for the Cyber Heist game and session tables.

These classes follow database/schema.sql. SQLite may show DATETIME in the
SQLAlchemy-created database and TEXT in the hand-written script. Both store
UTC timestamp strings. The column names, keys, and relationships match.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from database import Base


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    attempts = relationship("PuzzleAttempt", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)


class Mission(Base):
    __tablename__ = "missions"
    __table_args__ = (
        CheckConstraint("mission_order >= 1", name="ck_mission_order_positive"),
    )

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    topic = Column(String, nullable=False)
    mission_order = Column(Integer, unique=True, nullable=False)
    is_mvp = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at = Column(
        DateTime,
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    puzzles = relationship(
        "Puzzle",
        back_populates="mission",
        order_by="Puzzle.puzzle_order",
    )
    progress = relationship("UserProgress", back_populates="mission")


class Puzzle(Base):
    __tablename__ = "puzzles"
    __table_args__ = (
        UniqueConstraint("mission_id", "puzzle_order", name="uq_puzzle_mission_order"),
        CheckConstraint("points >= 0", name="ck_puzzle_points_nonnegative"),
        CheckConstraint("puzzle_order >= 1", name="ck_puzzle_order_positive"),
    )

    id = Column(Integer, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    puzzle_type = Column(String, nullable=False)
    instructions = Column(Text, nullable=False)
    solution_hash = Column(String, nullable=False)
    points = Column(Integer, nullable=False)
    puzzle_order = Column(Integer, nullable=False)

    mission = relationship("Mission", back_populates="puzzles")
    attempts = relationship("PuzzleAttempt", back_populates="puzzle")


class PuzzleAttempt(Base):
    __tablename__ = "puzzle_attempts"
    __table_args__ = (
        CheckConstraint("points_earned >= 0", name="ck_attempt_points_nonnegative"),
        CheckConstraint(
            "is_correct = 1 OR points_earned = 0",
            name="ck_attempt_points_only_if_correct",
        ),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    puzzle_id = Column(Integer, ForeignKey("puzzles.id"), nullable=False, index=True)
    is_correct = Column(Boolean, nullable=False)
    points_earned = Column(Integer, nullable=False, default=0, server_default=text("0"))
    attempted_at = Column(DateTime, nullable=False, default=utc_now)

    user = relationship("User", back_populates="attempts")
    puzzle = relationship("Puzzle", back_populates="attempts")


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "mission_id", name="uq_user_mission_progress"),
        CheckConstraint(
            "status IN ('locked', 'available', 'in_progress', 'completed')",
            name="ck_user_progress_status",
        ),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False, index=True)
    status = Column(String, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="progress")
    mission = relationship("Mission", back_populates="progress")
