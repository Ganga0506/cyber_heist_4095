"""Account sessions and server-authoritative MVP gameplay."""

import hashlib
import logging
import os
import re
import secrets
import sqlite3
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from console_expression import MAX_SOURCE_CHARS, ConsoleRejected, ConsoleSyntaxError, ConsoleTimeout, check_source
from console_guard import console_gate
from models import AccountMfa, AuthSession, HintPurchase, LessonDraft, Mission, Puzzle, PuzzleAttempt, User, UserProgress, utc_now
from economy import challenge, puzzle_reward_totals
from learning import lesson_for, run_cases, skipped_cases
from mfa import accept_factor
from schemas import PlayerProgress, ProgressItem
from security import DUMMY_PASSWORD_HASH, breached_password, hash_password, hash_solution, password_needs_rehash, verify_password
from seed import DEMO_USERS

router = APIRouter(prefix="/api")
bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger("uvicorn.error.security")
SESSION_LIFETIME = timedelta(hours=8)
STARTING_COINS = 20
MISSION_COIN_REWARD = 10
EMAIL_PATTERN = re.compile(r"[a-z0-9._%+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+")


class RequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PasswordCredentials(RequestBody):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().casefold()


class LoginBody(PasswordCredentials):
    mfa_code: str | None = Field(default=None, max_length=32)


class RegisterBody(PasswordCredentials):
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
        if not EMAIL_PATTERN.fullmatch(value):
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


class CodeBody(RequestBody):
    action: Literal["save", "run", "submit"]
    code: str = Field(max_length=MAX_SOURCE_CHARS)

    @field_validator("code")
    @classmethod
    def bounded_source(cls, value):
        return check_source(value)


class UserPublic(BaseModel):
    id: int
    username: str


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = int(SESSION_LIFETIME.total_seconds())
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
    coins_awarded: int = 0


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue_session(db, user):
    db.query(AuthSession).filter(AuthSession.expires_at <= utc_now()).delete()
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token_hash=token_digest(token), user_id=user.id,
                       expires_at=utc_now() + SESSION_LIFETIME))
    return SessionResponse(access_token=token, user=UserPublic(id=user.id, username=user.username))


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
    drafts = {}
    purchased = {}
    if row.status != "locked":
        drafts = dict(db.query(LessonDraft.puzzle_id, LessonDraft.code)
                      .filter_by(user_id=row.user_id).all())
        for purchase in db.query(HintPurchase).join(Puzzle).filter(
            HintPurchase.user_id == row.user_id, Puzzle.mission_id == mission.id
        ).order_by(HintPurchase.hint_index):
            purchased.setdefault(purchase.puzzle_id, []).append(purchase.hint_index)
    puzzles = []
    if row.status != "locked":
        for puzzle in db.query(Puzzle).filter_by(mission_id=mission.id).order_by(Puzzle.puzzle_order):
            reward, prices, hints = challenge(mission, puzzle)
            puzzles.append({"puzzle_id": puzzle.id, "solved": puzzle.id in best,
                            "points_earned": best.get(puzzle.id, 0), "draft": drafts.get(puzzle.id),
                            "coin_reward": reward, "hint_prices": prices,
                            "purchased_hints": [hints[index] for index in purchased.get(puzzle.id, [])]})
    return ProgressItem(
        mission_id=mission.id, title=mission.title, mission_order=mission.mission_order,
        status=row.status, completed_at=(row.completed_at.isoformat() + "Z") if row.completed_at else None,
        puzzles=puzzles,
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


def check_password_corpus(password):
    try:
        blocked = breached_password(password)
    except (sqlite3.Error, RuntimeError):
        logger.error("password_screening_unavailable")
        raise HTTPException(503, "Password screening is temporarily unavailable") from None
    if blocked:
        raise HTTPException(422, "Choose a password that has not appeared in known breaches")


@router.post("/auth/register", status_code=201, response_model=UserPublic)
def register(body: RegisterBody, db: Session = Depends(get_db)):
    if os.getenv("CYBERHEIST_ENV") == "production" and any(body.email == row["email"] for row in DEMO_USERS):
        raise HTTPException(409, "Username or email already registered")
    check_password_corpus(body.password)
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
    stored_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    valid = verify_password(body.password, stored_hash)
    if user is None or not valid:
        logger.info("password_login_failed")
        raise HTTPException(401, "Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
    replacement = hash_password(body.password) if password_needs_rehash(stored_hash) else None
    lock_player(db, user)
    db.refresh(user)
    if user.password_hash != stored_hash and not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
    accept_factor(db, db.get(AccountMfa, user.id), body.mfa_code)
    if replacement:
        db.query(User).filter_by(id=user.id, password_hash=stored_hash).update({"password_hash": replacement})
    sync_progress(db, user)
    result = issue_session(db, user)
    db.commit()
    return result


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(current_user)):
    return {"id": user.id, "username": user.username}


@router.post("/auth/logout", status_code=204)
def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer),
           user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.query(AuthSession).filter_by(token_hash=token_digest(credentials.credentials),
                                   user_id=user.id).delete()
    db.commit()
    return Response(status_code=204)


@router.post("/auth/logout-all", status_code=204)
def logout_all(user: User = Depends(current_user), db: Session = Depends(get_db)):
    lock_player(db, user)
    db.query(AuthSession).filter_by(user_id=user.id).delete()
    db.commit()
    return Response(status_code=204)


@router.get("/me/progress", response_model=PlayerProgress)
def progress(user: User = Depends(current_user), db: Session = Depends(get_db)):
    lock_player(db, user)
    rows, best = sync_progress(db, user)
    result = PlayerProgress(username=user.username, score=sum(best.values()), puzzles_solved=len(best),
                            coins=coin_balance(db, user.id),
                            mission_coin_reward=MISSION_COIN_REWARD,
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
    puzzle, mission, row, best = started_puzzle(db, user, puzzle_id)
    if lesson_for(puzzle):
        raise HTTPException(422, "Submit Python code for this lesson")
    correct = secrets.compare_digest(hash_solution(body.answer), puzzle.solution_hash)
    return record_attempt(db, user, puzzle, mission, row, best, correct)


@router.post("/puzzles/{puzzle_id}/code")
def lesson_code(puzzle_id: int, body: CodeBody, user: User = Depends(current_user), db: Session = Depends(get_db)):
    with console_gate.admit(user.id, execute=body.action != "save"):
        return handle_lesson_code(db, user, puzzle_id, body)


def handle_lesson_code(db, user, puzzle_id, body):
    puzzle, mission, row, best = started_lesson(db, user, puzzle_id)
    if body.action != "save":
        try:
            report = run_cases(puzzle.puzzle_order, body.code, final=body.action == "submit")
        except ConsoleSyntaxError as error:
            report = skipped_cases(puzzle.puzzle_order, str(error), "syntax_error")
        except ConsoleRejected as error:
            console_gate.policy_rejection()
            report = skipped_cases(puzzle.puzzle_order, str(error), "blocked")
        except ConsoleTimeout:
            logger.warning("console_evaluation_stopped reason=deadline")
            raise HTTPException(503, "Console evaluation timed out. Try again shortly.") from None
        except Exception:
            logger.error("console_evaluation_stopped reason=internal_error")
            raise HTTPException(503, "Console evaluation is temporarily unavailable") from None
    draft = db.get(LessonDraft, (user.id, puzzle.id))
    if draft is None:
        db.add(LessonDraft(user_id=user.id, puzzle_id=puzzle.id, code=body.code))
    else:
        draft.code = body.code
    if body.action == "save":
        db.commit()
        return {"saved": True}
    if body.action == "submit":
        result = record_attempt(db, user, puzzle, mission, row, best, report["passed"])
        return {**report, "attempt": result}
    db.commit()
    return report


def completed_mission_progress(db):
    return db.query(UserProgress).join(Mission).filter(
        UserProgress.status == "completed", Mission.is_mvp.is_(True)
    )


def coin_balance(db, user_id):
    completed = completed_mission_progress(db).filter(UserProgress.user_id == user_id).count()
    rewards = puzzle_reward_totals(db, user_id).one_or_none()
    spent = db.query(func.coalesce(func.sum(HintPurchase.price), 0)).filter_by(user_id=user_id).scalar()
    return STARTING_COINS + completed * MISSION_COIN_REWARD + (rewards.coins if rewards else 0) - spent


@router.post("/puzzles/{puzzle_id}/hints/{number}")
def buy_hint(puzzle_id: int, number: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    puzzle, mission, _, best = started_puzzle(db, user, puzzle_id)
    if lesson_for(puzzle):
        check_lesson_order(db, puzzle, mission, best)
    _, prices, hints = challenge(mission, puzzle)
    index = number - 1
    if not 0 <= index < len(hints):
        raise HTTPException(404, "Hint not found")
    price = prices[index]
    balance = coin_balance(db, user.id)
    if db.get(HintPurchase, (user.id, puzzle.id, index)) is None:
        if index and db.get(HintPurchase, (user.id, puzzle.id, index - 1)) is None:
            raise HTTPException(409, "Buy the previous hint first")
        if balance < price:
            raise HTTPException(409, "You need more coins to buy this hint")
        db.add(HintPurchase(user_id=user.id, puzzle_id=puzzle.id, hint_index=index, price=price))
        balance -= price
    db.commit()
    return {"hint": hints[index], "coins": balance}


def started_lesson(db, user, puzzle_id):
    puzzle, mission, row, best = started_puzzle(db, user, puzzle_id)
    if not lesson_for(puzzle):
        raise HTTPException(404, "Coding lesson not found")
    check_lesson_order(db, puzzle, mission, best)
    return puzzle, mission, row, best


def check_lesson_order(db, puzzle, mission, best):
    previous = db.query(Puzzle.id).filter(Puzzle.mission_id == mission.id,
                                          Puzzle.puzzle_order < puzzle.puzzle_order)
    if puzzle.id not in best and any(previous_id not in best for (previous_id,) in previous):
        raise HTTPException(403, "Complete the previous lesson first")


def started_puzzle(db, user, puzzle_id):
    lock_player(db, user)
    puzzle = db.get(Puzzle, puzzle_id)
    if puzzle is None:
        raise HTTPException(404, "Puzzle not found")
    mission, row, best = accessible_mission(db, user, puzzle.mission_id)
    if row.status == "available":
        raise HTTPException(409, "Start the mission first")
    return puzzle, mission, row, best


def record_attempt(db, user, puzzle, mission, row, best, correct):
    before = {r.mission_id: r.status for r in db.query(UserProgress).filter_by(user_id=user.id)}
    solved = puzzle.id in best
    award = puzzle.points if correct and not solved else 0
    record = PuzzleAttempt(user_id=user.id, puzzle_id=puzzle.id, is_correct=correct, points_earned=award)
    db.add(record)
    db.flush()
    rows, best = sync_progress(db, user)
    puzzle_reward = challenge(mission, puzzle)[0] if correct and not solved else 0
    mission_reward = MISSION_COIN_REWARD if mission.is_mvp and before[mission.id] != "completed" and row.status == "completed" else 0
    result = AttemptResponse(
        attempt_id=record.id, puzzle_id=puzzle.id, is_correct=correct, already_solved=solved,
        points_awarded=award, total_score=sum(best.values()),
        mission=progress_item(db, mission, row, best),
        unlocked_mission_ids=[m.id for m, r in rows if before[m.id] == "locked" and r.status == "available"],
        coins_awarded=puzzle_reward + mission_reward,
    )
    db.commit()
    return result
