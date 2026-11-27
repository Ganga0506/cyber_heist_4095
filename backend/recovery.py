"""Single-use, email-delivered password recovery for password accounts."""

import os
import secrets
import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import Field
from sqlalchemy import delete, func
from sqlalchemy.orm import Session

from database import get_db
from gameplay import EMAIL_PATTERN, RequestBody, check_password_corpus, lock_player, logger, token_digest
from google_signin import public_origin
from models import AccountMfa, AuthSession, GoogleIdentity, PasswordReset, User, utc_now
from security import hash_password

router = APIRouter(prefix="/api/auth/recovery")
RESET_LIFETIME = timedelta(minutes=15)


class RequestReset(RequestBody):
    email: str = Field(min_length=3, max_length=254)


class CompleteReset(RequestBody):
    token: str = Field(min_length=43, max_length=43, pattern=r"^[A-Za-z0-9_-]+$")
    password: str = Field(min_length=12, max_length=128)


def recovery_config():
    host, sender, user, password = (
        os.getenv(key) for key in ("SMTP_HOST", "SMTP_FROM", "SMTP_USER", "SMTP_PASSWORD")
    )
    if not all((host, sender, user, password)):
        raise HTTPException(404, "Password recovery is unavailable")
    return host, sender, user, password, public_origin()


def send_reset(email, token, config):
    host, sender, user, password, origin = config
    message = EmailMessage()
    message["From"] = sender
    message["To"] = email
    message["Subject"] = "Reset your Cyber Heist password"
    message.set_content(
        "This one-time link expires in 15 minutes.\n\n"
        f"{origin}/#/reset-password/{token}\n\n"
        "If you did not request this, you can ignore the email."
    )
    try:
        with smtplib.SMTP_SSL(host, 465, timeout=5, context=ssl.create_default_context()) as smtp:
            smtp.login(user, password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.error("password_recovery_delivery_failed")


@router.post("/request", status_code=202)
def request_reset(body: RequestReset, background: BackgroundTasks, db: Session = Depends(get_db)):
    config = recovery_config()
    email = body.email.strip().casefold()
    user = db.query(User).filter(func.lower(User.email) == email).one_or_none()
    if user and EMAIL_PATTERN.fullmatch(email) and not db.query(GoogleIdentity).filter_by(user_id=user.id).first():
        lock_player(db, user)
        existing = db.query(PasswordReset).filter_by(user_id=user.id).one_or_none()
        now = utc_now()
        if existing is None or existing.expires_at <= now:
            if existing:
                db.delete(existing)
                db.flush()
            token = secrets.token_urlsafe(32)
            db.add(PasswordReset(token_hash=token_digest(token), user_id=user.id,
                                 expires_at=now + RESET_LIFETIME))
            background.add_task(send_reset, email, token, config)
        db.commit()
    return {"accepted": True}


@router.post("/complete", status_code=204)
def complete_reset(body: CompleteReset, db: Session = Depends(get_db)):
    recovery_config()
    check_password_corpus(body.password)
    digest = token_digest(body.token)
    pending = db.get(PasswordReset, digest)
    if pending is None or pending.expires_at <= utc_now():
        raise HTTPException(400, "Recovery link is invalid or expired")
    replacement = hash_password(body.password)
    user_id = db.execute(
        delete(PasswordReset).where(PasswordReset.token_hash == digest,
                                    PasswordReset.expires_at > utc_now())
        .returning(PasswordReset.user_id)
    ).scalar_one_or_none()
    if user_id is None:
        raise HTTPException(400, "Recovery link is invalid or expired")
    user = db.get(User, user_id)
    user.password_hash = replacement
    factor = db.get(AccountMfa, user_id)
    if factor is not None:
        factor.pending = factor.pending_expires_at = None
    db.query(AuthSession).filter_by(user_id=user_id).delete()
    db.commit()
