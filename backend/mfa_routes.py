"""Authenticated management for optional password-account MFA."""

import secrets

import pyotp
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import Field
from sqlalchemy.orm import Session

from database import get_db
from gameplay import RequestBody, bearer, current_user, lock_player, token_digest
from mfa import (SETUP_LIFETIME, accept_factor, check_attempt_budget, decrypt_secret,
                 encrypt_secret, matching_step, mfa_encryption, record_failure, recovery_digest)
from models import AccountMfa, AuthSession, GoogleIdentity, User, utc_now
from security import verify_password

router = APIRouter(prefix="/api/auth/mfa")


class PasswordBody(RequestBody):
    password: str = Field(min_length=1, max_length=128)


class SetupCode(RequestBody):
    code: str = Field(pattern=r"^[0-9]{6}$")


class DisableBody(PasswordBody):
    code: str = Field(min_length=1, max_length=32)


def require_password(db, user, password):
    lock_player(db, user)
    db.refresh(user)
    if db.query(GoogleIdentity).filter_by(user_id=user.id).first():
        raise HTTPException(403, "Manage this account's MFA with Google")
    if not verify_password(password, user.password_hash):
        raise HTTPException(403, "Current password is incorrect")


def revoke_other_sessions(db, user, credentials):
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.token_hash != token_digest(credentials.credentials),
    ).delete()


@router.get("")
def status(user: User = Depends(current_user), db: Session = Depends(get_db)):
    factor = db.get(AccountMfa, user.id)
    return {
        "available": mfa_encryption() is not None and not db.query(GoogleIdentity).filter_by(user_id=user.id).first(),
        "enabled": bool(factor and factor.secret),
    }


@router.post("/start")
def start_enrollment(body: PasswordBody, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_password(db, user, body.password)
    factor = db.get(AccountMfa, user.id)
    if factor and factor.secret:
        raise HTTPException(409, "Authenticator is already enabled")
    if factor is None:
        factor = AccountMfa(user_id=user.id)
        db.add(factor)
    secret = pyotp.random_base32()
    factor.pending = encrypt_secret(secret)
    factor.pending_expires_at = utc_now() + SETUP_LIFETIME
    db.commit()
    return {"secret": secret}


@router.post("/confirm")
def confirm_enrollment(
    body: SetupCode, user: User = Depends(current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)
):
    lock_player(db, user)
    active_session = db.query(AuthSession.token_hash).filter(
        AuthSession.token_hash == token_digest(credentials.credentials),
        AuthSession.user_id == user.id,
        AuthSession.expires_at > utc_now(),
    ).first()
    if not active_session:
        raise HTTPException(401, "Session missing or expired")
    factor = db.get(AccountMfa, user.id)
    if not factor or not factor.pending or factor.pending_expires_at <= utc_now():
        raise HTTPException(409, "Start authenticator setup again")
    check_attempt_budget(factor)
    step = matching_step(decrypt_secret(factor.pending), body.code, -1)
    if step is None:
        record_failure(db, factor)
        raise HTTPException(422, "Invalid authenticator code")
    codes = [secrets.token_urlsafe(18) for _ in range(10)]
    factor.secret = factor.pending
    factor.pending = factor.pending_expires_at = None
    factor.last_step = step
    factor.failures = 0
    factor.recovery_hashes = [recovery_digest(code) for code in codes]
    revoke_other_sessions(db, user, credentials)
    db.commit()
    return {"recovery_codes": codes}


@router.post("/disable", status_code=204)
def disable(
    body: DisableBody, user: User = Depends(current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)
):
    require_password(db, user, body.password)
    factor = db.get(AccountMfa, user.id)
    if not factor or not factor.secret:
        raise HTTPException(409, "Authenticator is not enabled")
    accept_factor(db, factor, body.code, failure_status=403)
    db.delete(factor)
    revoke_other_sessions(db, user, credentials)
    db.commit()
