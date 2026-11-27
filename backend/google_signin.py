"""Google sign-in through a browser-bound, one-time authorization flow."""

import base64
import hashlib
import os
import secrets
from datetime import timedelta
from urllib.parse import urlencode, urlsplit

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from google.auth import exceptions as google_errors
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from database import get_db
from gameplay import SessionResponse, issue_session, logger, sync_progress, token_digest
from models import GoogleFlow, GoogleHandoff, GoogleIdentity, User, utc_now
from security import hash_password
from seed import DEMO_USERS

router = APIRouter(prefix="/api/auth/google")
FLOW_COOKIE = "__Host-cyberheist-google"
HANDOFF_COOKIE = "__Host-cyberheist-handoff"
CALLBACK = "/api/auth/google/callback"
GOOGLE_ISSUER = "https://accounts.google.com"


def public_origin():
    origin = os.getenv("CYBERHEIST_PUBLIC_ORIGIN", "")
    url = urlsplit(origin)
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.path or url.query or url.fragment or origin != f"https://{url.netloc}"):
        raise ValueError("CYBERHEIST_PUBLIC_ORIGIN must be a bare HTTPS origin")
    return origin


def configuration():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not secret:
        raise HTTPException(404, "Google sign-in is unavailable")
    return client_id, secret, public_origin()


def set_ticket(response, name, value, seconds):
    response.set_cookie(name, value, max_age=seconds, secure=True, httponly=True,
                        samesite="lax", path="/")


def clear_ticket(response, name):
    response.delete_cookie(name, path="/", secure=True, httponly=True, samesite="lax")


@router.get("/start")
def start(db: Session = Depends(get_db)):
    client_id, _, origin = configuration()
    state, verifier, nonce = (secrets.token_urlsafe(32) for _ in range(3))
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    now = utc_now()
    db.query(GoogleFlow).filter(GoogleFlow.expires_at <= now).delete()
    db.add(GoogleFlow(token_hash=token_digest(state), verifier=verifier, nonce=nonce,
                      expires_at=now + timedelta(minutes=5)))
    db.commit()
    query = urlencode({
        "client_id": client_id, "redirect_uri": origin + CALLBACK, "response_type": "code",
        "scope": "openid email", "state": state, "nonce": nonce,
        "code_challenge": challenge, "code_challenge_method": "S256",
    })
    response = RedirectResponse(f"{GOOGLE_ISSUER}/o/oauth2/v2/auth?{query}", 303)
    set_ticket(response, FLOW_COOKIE, state, 300)
    return response


def verify_google(code, verifier, nonce, client_id, secret, origin):
    with requests.Session() as http:
        http.trust_env = False
        response = http.post("https://oauth2.googleapis.com/token", data={
            "code": code, "code_verifier": verifier, "client_id": client_id,
            "client_secret": secret, "redirect_uri": origin + CALLBACK,
            "grant_type": "authorization_code",
        }, timeout=(3, 5), allow_redirects=False)
        response.raise_for_status()
        transport = GoogleRequest(session=http)

        def fetch_certificate(url, **kwargs):
            kwargs["timeout"] = 5
            kwargs["allow_redirects"] = False
            return transport(url, **kwargs)

        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("id_token"), str):
            raise ValueError("Google did not return an identity token")
        claims = id_token.verify_oauth2_token(data["id_token"], fetch_certificate, client_id)
    if claims.get("nonce") != nonce or claims.get("email_verified") is not True:
        raise ValueError("Unverified Google identity")
    subject, email = claims.get("sub"), claims.get("email")
    if not isinstance(subject, str) or not 1 <= len(subject) <= 255:
        raise ValueError("Invalid subject")
    if not isinstance(email, str) or not 1 <= len(email) <= 254 or "@" not in email:
        raise ValueError("Invalid email")
    return subject, email.strip().casefold()


def google_user(db, subject, email):
    identity = db.get(GoogleIdentity, subject)
    if identity:
        return db.get(User, identity.user_id)
    if any(email == row["email"] for row in DEMO_USERS) or db.query(User.id).filter(func.lower(User.email) == email).first():
        raise ValueError("Existing account requires separate verified linking")
    user = User(username="agent-" + secrets.token_hex(8), email=email,
                password_hash=hash_password(secrets.token_urlsafe(48)))
    db.add(user)
    db.flush()
    db.add(GoogleIdentity(subject=subject, user_id=user.id))
    return user


@router.get("/callback")
def callback(request: Request, db: Session = Depends(get_db)):
    client_id, secret, origin = configuration()
    state = request.query_params.get("state", "")
    code = request.query_params.get("code", "")
    browser_state = request.cookies.get(FLOW_COOKIE, "")
    failure = RedirectResponse(origin + "/#/google-error", 303)
    clear_ticket(failure, FLOW_COOKIE)
    if (not 1 <= len(code) <= 2048 or len(state) != 43 or not state.isascii()
            or not browser_state.isascii() or not secrets.compare_digest(state, browser_state)):
        logger.info("google_signin_rejected reason=invalid_callback")
        return failure
    flow = db.execute(
        delete(GoogleFlow).where(GoogleFlow.token_hash == token_digest(state),
                                 GoogleFlow.expires_at > utc_now())
        .returning(GoogleFlow.verifier, GoogleFlow.nonce)
    ).one_or_none()
    db.commit()
    if not flow:
        return failure
    try:
        subject, email = verify_google(code, flow.verifier, flow.nonce, client_id, secret, origin)
        user = google_user(db, subject, email)
        sync_progress(db, user)
        ticket = secrets.token_urlsafe(32)
        now = utc_now()
        db.query(GoogleHandoff).filter(GoogleHandoff.expires_at <= now).delete()
        db.add(GoogleHandoff(token_hash=token_digest(ticket), user_id=user.id,
                             expires_at=now + timedelta(seconds=60)))
        db.commit()
    except (requests.RequestException, google_errors.GoogleAuthError, ValueError, KeyError, IntegrityError):
        db.rollback()
        logger.info("google_signin_rejected reason=identity_or_provider")
        return failure
    success = RedirectResponse(origin + "/#/google", 303)
    clear_ticket(success, FLOW_COOKIE)
    set_ticket(success, HANDOFF_COOKIE, ticket, 60)
    return success


@router.post("/session", response_model=SessionResponse)
def exchange(request: Request, response: Response, db: Session = Depends(get_db)):
    _, _, origin = configuration()
    if request.headers.get("origin") != origin:
        raise HTTPException(403, "Invalid request origin")
    ticket = request.cookies.get(HANDOFF_COOKIE, "")
    if len(ticket) != 43:
        raise HTTPException(401, "Sign-in link expired")
    user_id = db.execute(
        delete(GoogleHandoff).where(GoogleHandoff.token_hash == token_digest(ticket),
                                    GoogleHandoff.expires_at > utc_now())
        .returning(GoogleHandoff.user_id)
    ).scalar_one_or_none()
    if not user_id:
        raise HTTPException(401, "Sign-in link expired")
    session = issue_session(db, db.get(User, user_id))
    db.commit()
    clear_ticket(response, HANDOFF_COOKIE)
    return session
