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
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import AccountMfa, Mission, Puzzle, PuzzleAttempt, User, UserProgress
from schemas import (
    HealthResponse,
    LeaderboardResponse,
    MissionDetail,
    MissionSummary,
    PuzzlePublic,
)
from seed import DEMO_USERS, init_db, seed
from database import SessionLocal
from gameplay import MISSION_COIN_REWARD, accessible_mission, completed_mission_progress, current_user, router
from learning import lesson_for
from economy import puzzle_reward_totals
from google_signin import public_origin, router as google_router
from request_guard import RequestGuard
from recovery import router as recovery_router
from mfa import mfa_encryption
from mfa_routes import router as mfa_router
from security import breached_password

PRODUCTION = os.getenv("CYBERHEIST_ENV") == "production"

# Local Vite origins only. Add a new origin here and in README.md together.
LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

SCORING_NOTE = (
    "Rank is based on lifetime puzzle and mission coins, then distinct solved puzzles and username. "
    "The legacy score field is calculated from puzzle_attempts."
)



@asynccontextmanager
async def lifespan(_app: FastAPI):
    if PRODUCTION:
        public_origin()
        breached_password("startup-corpus-probe")
        if not os.getenv("DATABASE_URL") or ":memory:" in os.environ["DATABASE_URL"]:
            raise RuntimeError("Production requires an explicit persistent DATABASE_URL")
        init_db()
        with SessionLocal() as db:
            if mfa_encryption() is None and db.query(AccountMfa).filter(AccountMfa.secret.is_not(None)).first():
                raise RuntimeError("Production has MFA accounts but no authenticator encryption key")
            if db.query(User.id).filter(User.email.in_([row["email"] for row in DEMO_USERS])).first():
                raise RuntimeError("Production database contains development accounts")
            seed(db, demo=False)
    # Tests set this to 0 so pytest does not create the development database.
    elif os.getenv("CYBERHEIST_AUTO_CREATE", "1") != "0":
        init_db()
        with SessionLocal() as db:
            seed(db)
    yield


app = FastAPI(
    title="Cyber Heist API",
    version="0.1.0",
    summary="Early prototype for the Cyber Heist escape-room game.",
    lifespan=lifespan,
    docs_url=None if PRODUCTION else "/docs",
    redoc_url=None if PRODUCTION else "/redoc",
    openapi_url=None if PRODUCTION else "/openapi.json",
)

app.add_middleware(RequestGuard, production=PRODUCTION)
if PRODUCTION:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[urlsplit(public_origin()).hostname])
app.add_middleware(
    CORSMiddleware,
    allow_origins=[public_origin()] if PRODUCTION else LOCAL_FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(_request, error):
    return JSONResponse({"detail": [
        {"loc": item["loc"], "msg": item["msg"]} if item["type"] != "extra_forbidden"
        else {"loc": ["body"], "msg": "Unexpected field"}
        for item in error.errors()
    ]}, status_code=422)


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
        puzzles=[
            PuzzlePublic.model_validate(puzzle).model_copy(update={"lesson": lesson_for(puzzle)})
            for puzzle in puzzles
        ],
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
    rewards = (
        completed_mission_progress(db)
        .with_entities(UserProgress.user_id, (func.count() * MISSION_COIN_REWARD).label("coins"))
        .group_by(UserProgress.user_id)
        .subquery()
    )
    puzzle_rewards = puzzle_reward_totals(db).subquery()
    coins = func.coalesce(rewards.c.coins, 0) + func.coalesce(puzzle_rewards.c.coins, 0)
    rows = (
        db.query(User.username, score.label("score"), solved.label("puzzles_solved"), coins.label("coins_earned"))
        .outerjoin(best_attempt, best_attempt.c.user_id == User.id)
        .outerjoin(rewards, rewards.c.user_id == User.id)
        .outerjoin(puzzle_rewards, puzzle_rewards.c.user_id == User.id)
        .group_by(User.id, User.username, rewards.c.coins, puzzle_rewards.c.coins)
        .order_by(coins.desc(), solved.desc(), User.username.asc())
        .all()
    )
    entries = [
        {
            "rank": index,
            "username": row.username,
            "score": int(row.score or 0),
            "puzzles_solved": int(row.puzzles_solved or 0),
            "coins_earned": row.coins_earned,
        }
        for index, row in enumerate(rows, start=1)
    ]
    return LeaderboardResponse(scoring=SCORING_NOTE, entries=entries)



app.include_router(router)
app.include_router(google_router)
app.include_router(recovery_router)
app.include_router(mfa_router)
