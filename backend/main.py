"""Cyber Heist API.

Week 2 prototype routes:
- GET /api/health
- GET /api/missions
- GET /api/missions/{mission_id}
- GET /api/leaderboard
- GET /api/me/progress   (bearer session)

Account and gameplay routes are registered from gameplay.py.
Scores are calculated by the server.
"""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Mission, Puzzle, PuzzleAttempt, User, UserProgress
from schemas import (
    HealthResponse,
    LeaderboardResponse,
    MissionDetail,
    MissionSummary,
    PuzzlePublic,
)
from seed import init_db, seed
from database import SessionLocal
from gameplay import router, current_user, accessible_mission

# Local Vite origins only. Add a new origin here and in README.md together.
LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

SCORING_NOTE = (
    "Score is the sum of each player's best correct attempt on each puzzle. "
    "A repeated correct attempt does not increase the score. The total is "
    "calculated from puzzle_attempts and is not stored on the user."
)



@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Tests set this to 0 so pytest does not create the development database.
    if os.getenv("CYBERHEIST_AUTO_CREATE", "1") != "0":
        init_db()
        with SessionLocal() as db:
            seed(db)
    yield


app = FastAPI(
    title="Cyber Heist API",
    version="0.1.0",
    summary="Early prototype for the Cyber Heist escape-room game.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/")
def root():
    return {
        "name": "Cyber Heist API",
        "health": "/api/health",
        "docs": "/docs",
    }


@app.get("/api/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    try:
        db.query(Mission.id).limit(1).all()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return HealthResponse(status="ok", database="connected")


@app.get("/api/missions", response_model=list[MissionSummary])
def list_missions(db: Session = Depends(get_db)):
    counts = dict(
        db.query(Puzzle.mission_id, func.count(Puzzle.id)).group_by(Puzzle.mission_id).all()
    )
    missions = db.query(Mission).order_by(Mission.mission_order).all()
    return [
        MissionSummary(
            id=mission.id,
            title=mission.title,
            description=mission.description,
            topic=mission.topic,
            mission_order=mission.mission_order,
            is_mvp=bool(mission.is_mvp),
            puzzle_count=int(counts.get(mission.id, 0)),
        )
        for mission in missions
    ]


@app.get("/api/missions/{mission_id}", response_model=MissionDetail)
def get_mission(mission_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    accessible_mission(db, user, mission_id)
    mission = db.query(Mission).filter(Mission.id == mission_id).one_or_none()
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    puzzles = (
        db.query(Puzzle)
        .filter(Puzzle.mission_id == mission.id)
        .order_by(Puzzle.puzzle_order)
        .all()
    )
    return MissionDetail(
        id=mission.id,
        title=mission.title,
        description=mission.description,
        topic=mission.topic,
        mission_order=mission.mission_order,
        is_mvp=bool(mission.is_mvp),
        puzzle_count=len(puzzles),
        puzzles=[PuzzlePublic.model_validate(puzzle) for puzzle in puzzles],
    )


@app.get("/api/leaderboard", response_model=LeaderboardResponse)
def leaderboard(db: Session = Depends(get_db)):
    best_attempt = (
        db.query(
            PuzzleAttempt.user_id.label("user_id"),
            PuzzleAttempt.puzzle_id.label("puzzle_id"),
            func.max(PuzzleAttempt.points_earned).label("points"),
        )
        .filter(PuzzleAttempt.is_correct.is_(True))
        .group_by(PuzzleAttempt.user_id, PuzzleAttempt.puzzle_id)
        .subquery()
    )
    score = func.coalesce(func.sum(best_attempt.c.points), 0)
    solved = func.coalesce(func.count(best_attempt.c.puzzle_id), 0)
    rows = (
        db.query(User.username, score.label("score"), solved.label("puzzles_solved"))
        .outerjoin(best_attempt, best_attempt.c.user_id == User.id)
        .group_by(User.id, User.username)
        .order_by(score.desc(), User.username.asc())
        .all()
    )
    entries = [
        {
            "rank": index,
            "username": row.username,
            "score": int(row.score or 0),
            "puzzles_solved": int(row.puzzles_solved or 0),
        }
        for index, row in enumerate(rows, start=1)
    ]
    return LeaderboardResponse(scoring=SCORING_NOTE, entries=entries)



app.include_router(router)
