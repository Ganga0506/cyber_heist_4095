"""API response shapes.

Puzzle solutions, password hashes, and email addresses are intentionally
absent. Adding them here would publish them through the FastAPI routes.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    database: str


class PuzzlePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    puzzle_type: str
    instructions: str
    points: int
    puzzle_order: int


class MissionSummary(BaseModel):
    id: int
    title: str
    description: str
    topic: str
    mission_order: int
    is_mvp: bool
    puzzle_count: int


class MissionDetail(MissionSummary):
    puzzles: list[PuzzlePublic]


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    score: int
    puzzles_solved: int


class LeaderboardResponse(BaseModel):
    scoring: str
    entries: list[LeaderboardEntry]


class ProgressItem(BaseModel):
    mission_id: int
    title: str
    mission_order: int
    status: str
    completed_at: datetime | None


class PlayerProgress(BaseModel):
    username: str
    missions: list[ProgressItem]
