"""Account sessions and server-authoritative MVP gameplay."""

import hashlib
import re
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import AuthSession, Mission, Puzzle, PuzzleAttempt, User, UserProgress, utc_now
from schemas import PlayerProgress, ProgressItem
from security import hash_password, hash_solution, verify_password

router = APIRouter(prefix="/api")
bearer = HTTPBearer(auto_error=False)


class RequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginBody(RequestBody):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().casefold()


class RegisterBody(LoginBody):
    password: str = Field(min_length=12, max_length=128)
    email: str = Field(max_length=254)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value):
        if not re.fullmatch(r"[a-z0-9_.-]{3,32}", value):
            raise ValueError("Use 3-32 letters, digits, dots, underscores or hyphens")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        value = value.strip().casefold()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value


class AnswerBody(RequestBody):
    answer: str = Field(min_length=1, max_length=4096)

    @field_validator("answer")
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError("Answer cannot be blank")
        return value


class UserPublic(BaseModel):
    id: int
    username: str


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: UserPublic


class AttemptResponse(BaseModel):
    attempt_id: int
    puzzle_id: int
    is_correct: bool
    already_solved: bool
    points_awarded: int
    total_score: int
    mission: ProgressItem
    unlocked_mission_ids: list[int]


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    session = db.get(AuthSession, token_digest(credentials.credentials)) if credentials else None
    if session is None or session.expires_at <= utc_now():
        raise HTTPException(401, "Session missing or expired", headers={"WWW-Authenticate": "Bearer"})
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(401, "Account not found")
    return user


def lock_player(db, user):
    # SQLite serializes writers. Acquire its write lock before reading gameplay
    # state so simultaneous correct answers cannot both report a new award.
    db.query(User).filter(User.id == user.id).update({User.username: User.username})


def best_points(db, user_id):
    return dict(db.query(PuzzleAttempt.puzzle_id, func.max(PuzzleAttempt.points_earned))
                .filter(PuzzleAttempt.user_id == user_id, PuzzleAttempt.is_correct.is_(True))
                .group_by(PuzzleAttempt.puzzle_id).all())


def sync_progress(db, user):
    """Reconcile old demo snapshots and initialize new mission rows."""
    best = best_points(db, user.id)
    missions = db.query(Mission).order_by(Mission.mission_order).all()
    previous_complete = True
    rows = []
    for mission in missions:
        row = db.query(UserProgress).filter_by(user_id=user.id, mission_id=mission.id).one_or_none()
        if row is None:
            row = UserProgress(user_id=user.id, mission_id=mission.id, status="locked")
            db.add(row)
        if mission.is_mvp:
            puzzles = db.query(Puzzle).filter_by(mission_id=mission.id).all()
            complete = bool(puzzles) and all(p.id in best for p in puzzles)
            if not previous_complete:
                row.status = "locked"
            elif complete:
                row.status = "completed"
                row.completed_at = row.completed_at or utc_now()
            elif row.status != "in_progress":
                row.status = "available"
            previous_complete = previous_complete and complete
        else:
            row.status = "locked"
        if row.status != "completed":
            row.completed_at = None
        rows.append((mission, row))
    db.flush()
    return rows, best


def progress_item(db, mission, row, best):
    return ProgressItem(
        mission_id=mission.id, title=mission.title, mission_order=mission.mission_order,
        status=row.status, completed_at=(row.completed_at.isoformat() + "Z") if row.completed_at else None,
        puzzles=[{"puzzle_id": p.id, "solved": p.id in best, "points_earned": best.get(p.id, 0)}
                 for p in db.query(Puzzle).filter_by(mission_id=mission.id).order_by(Puzzle.puzzle_order)]
        if row.status != "locked" else [],
    )


def accessible_mission(db, user, mission_id):
    rows, best = sync_progress(db, user)
    pair = next(((m, r) for m, r in rows if m.id == mission_id), None)
    if pair is None:
        raise HTTPException(404, "Mission not found")
    mission, row = pair
    if row.status == "locked":
        raise HTTPException(403, "Mission is locked or a later preview")
    return mission, row, best


@router.post("/auth/register", status_code=201, response_model=UserPublic)
def register(body: RegisterBody, db: Session = Depends(get_db)):
    duplicate = db.query(User).filter(
        (func.lower(User.username) == body.username) | (func.lower(User.email) == body.email)
    ).first()
    if duplicate:
        raise HTTPException(409, "Username or email already registered")
    user = User(username=body.username, email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.flush()
        sync_progress(db, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Username or email already registered")
    return {"id": user.id, "username": user.username}


@router.post("/auth/login", response_model=SessionResponse)
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.username) == body.username).first()
    # Hash even for an unknown account to avoid a cheap username timing check.
    valid = verify_password(body.password, user.password_hash) if user else verify_password(body.password, hash_password("unused-password"))
    if user is None or not valid:
        raise HTTPException(401, "Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token_hash=token_digest(token), user_id=user.id, expires_at=utc_now() + timedelta(days=1)))
    lock_player(db, user)
    sync_progress(db, user)
    db.commit()
    return SessionResponse(access_token=token, user=UserPublic(id=user.id, username=user.username))


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(current_user)):
    return {"id": user.id, "username": user.username}


@router.post("/auth/logout", status_code=204)
def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer),
           user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(db.get(AuthSession, token_digest(credentials.credentials)))
    db.commit()
    return Response(status_code=204)


@router.get("/me/progress", response_model=PlayerProgress)
def progress(user: User = Depends(current_user), db: Session = Depends(get_db)):
    lock_player(db, user)
    rows, best = sync_progress(db, user)
    result = PlayerProgress(username=user.username, score=sum(best.values()), puzzles_solved=len(best),
                            missions=[progress_item(db, m, r, best) for m, r in rows])
    db.commit()
    return result


@router.post("/missions/{mission_id}/start", response_model=ProgressItem)
def start(mission_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    lock_player(db, user)
    mission, row, best = accessible_mission(db, user, mission_id)
    if row.status == "available":
        row.status = "in_progress"
    result = progress_item(db, mission, row, best)
    db.commit()
    return result


@router.post("/puzzles/{puzzle_id}/attempts", response_model=AttemptResponse)
def attempt(puzzle_id: int, body: AnswerBody, user: User = Depends(current_user), db: Session = Depends(get_db)):
    lock_player(db, user)
    puzzle = db.get(Puzzle, puzzle_id)
    if puzzle is None:
        raise HTTPException(404, "Puzzle not found")
    mission, row, best = accessible_mission(db, user, puzzle.mission_id)
    if row.status == "available":
        raise HTTPException(409, "Start the mission first")
    before = {r.mission_id: r.status for r in db.query(UserProgress).filter_by(user_id=user.id)}
    correct = secrets.compare_digest(hash_solution(body.answer), puzzle.solution_hash)
    solved = puzzle.id in best
    award = puzzle.points if correct and not solved else 0
    record = PuzzleAttempt(user_id=user.id, puzzle_id=puzzle.id, is_correct=correct, points_earned=award)
    db.add(record)
    db.flush()
    rows, best = sync_progress(db, user)
    result = AttemptResponse(
        attempt_id=record.id, puzzle_id=puzzle.id, is_correct=correct, already_solved=solved,
        points_awarded=award, total_score=sum(best.values()),
        mission=progress_item(db, mission, row, best),
        unlocked_mission_ids=[m.id for m, r in rows if before[m.id] == "locked" and r.status == "available"],
    )
    db.commit()
    return result
