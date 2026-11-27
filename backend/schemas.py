"""API response shapes.

Puzzle solutions, password hashes, and email addresses are intentionally
absent. Adding them here would publish them through the FastAPI routes.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from learning import Lesson


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
    lesson: Lesson | None = None


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
    coins_earned: int


class LeaderboardResponse(BaseModel):
    scoring: str
    entries: list[LeaderboardEntry]


class ProgressItem(BaseModel):
    mission_id: int
    title: str
    mission_order: int
    status: str
    completed_at: datetime | None
    puzzles: list["PuzzleProgress"] = Field(default_factory=list)


class PuzzleProgress(BaseModel):
    puzzle_id: int
    solved: bool
    points_earned: int
    draft: str | None = None
    purchased_hints: list[str] = Field(default_factory=list)
    hint_prices: list[int] = Field(default_factory=list)
    coin_reward: int = 0


class PlayerProgress(BaseModel):
    username: str
    missions: list[ProgressItem]
    score: int = 0
    puzzles_solved: int = 0
    coins: int
    mission_coin_reward: int
