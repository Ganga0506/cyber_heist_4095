import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient
import pytest

import google_signin
from models import User
from request_guard import MAX_BODY, RequestGuard
from snapshot import copy_database


def test_password_hash_migrates_and_all_sessions_revoke(client, seeded_session):
    body = {"username": "nova.agent", "password": "dev-only-nova"}
    assert seeded_session.get(User, 1).password_hash.startswith("pbkdf2_sha256")
    first = client.post("/api/auth/login", json=body).json()
    second = client.post("/api/auth/login", json=body).json()
    seeded_session.expire_all()
    assert seeded_session.get(User, 1).password_hash.startswith("$argon2id$")
    assert first["access_token"] != second["access_token"]
    assert first["expires_in"] == 28_800

    def authorization(session):
        return {"Authorization": "Bearer " + session["access_token"]}

    assert client.post("/api/auth/logout-all", headers=authorization(first)).status_code == 204
    assert client.get("/api/me", headers=authorization(first)).status_code == 401
    assert client.get("/api/me", headers=authorization(second)).status_code == 401


def test_breached_password_screening_and_request_controls(client, monkeypatch, tmp_path):
    password = "fixture-breached-password"
    corpus = tmp_path / "breached.db"
    with sqlite3.connect(corpus) as db:
        db.execute("CREATE TABLE breached_passwords (digest TEXT PRIMARY KEY)")
        digest = hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest().upper()
        db.execute("INSERT INTO breached_passwords VALUES (?)", (digest,))
    monkeypatch.setenv("CYBERHEIST_BREACHED_PASSWORD_DB", str(corpus))
    body = {"username": "new.agent", "email": "new.agent@example.com", "password": password}
    assert client.post("/api/auth/register", json=body).status_code == 422
    monkeypatch.setenv("CYBERHEIST_BREACHED_PASSWORD_DB", str(tmp_path / "missing.db"))
    assert client.post("/api/auth/register", json=body).status_code == 503

    response = client.post("/api/auth/login", content=b"x" * (MAX_BODY + 1))
    assert response.status_code == 413
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"].startswith("default-src 'none'")
    assert client.post("/api/auth/login", data={"username": "new.agent"}).status_code == 415
    response = client.post("/api/auth/login", json={"username": "fixture", "password": password * 10})
    assert response.status_code == 422
    assert password not in response.text


def test_production_transport_and_rate_guard():
    async def endpoint(scope, receive, send):
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    guard = RequestGuard(endpoint, production=True)
    with closing(TestClient(guard, base_url="http://game.example")) as client:
        assert client.get("/api/health").status_code == 400
    with closing(TestClient(guard, base_url="https://game.example")) as client:
        for _ in range(20):
            response = client.post("/api/auth/login")
            assert response.status_code == 204
        assert response.headers["strict-transport-security"] == "max-age=31536000"
        response = client.post("/api/auth/login")
        assert response.status_code == 429
        assert response.headers["retry-after"] == "60"
        assert client.post("/api/missions/1/start").status_code == 204


def test_google_state_handoff_and_safe_account_linking(client, monkeypatch):
    origin = "https://game.example"
    monkeypatch.setenv("CYBERHEIST_PUBLIC_ORIGIN", origin)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")
    identity = ("subject-123", "new.agent@example.net")
    requests_seen = []

    def verify(code, verifier, nonce, client_id, secret, actual_origin):
        requests_seen.append((code, verifier, nonce))
        assert actual_origin == origin
        return identity

    monkeypatch.setattr(google_signin, "verify_google", verify)
    urls = origin + "/api/auth/google"

    def begin():
        response = client.get(urls + "/start", follow_redirects=False)
        assert response.status_code == 303
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "Secure" in response.headers["set-cookie"]
        query = parse_qs(urlsplit(response.headers["location"]).query)
        assert query["code_challenge_method"] == ["S256"]
        return query

    begin()
    callback = urls + "/callback"
    response = client.get(callback, params={"state": "wrong", "code": "temporary"}, follow_redirects=False)
    assert response.headers["location"].endswith("/#/google-error")
    assert not requests_seen

    query = begin()
    params = {"state": query["state"][0], "code": "temporary"}
    response = client.get(callback, params=params, follow_redirects=False)
    assert response.headers["location"] == origin + "/#/google"
    assert requests_seen[0][2] == query["nonce"][0]
    assert requests_seen[0][1] != query["code_challenge"][0]
    assert client.post(urls + "/session", headers={"Origin": "https://other.example"}).status_code == 403
    token = client.post(urls + "/session", headers={"Origin": origin}).json()["access_token"]
    assert client.get("/api/me", headers={"Authorization": "Bearer " + token}).status_code == 200
    assert client.post(urls + "/session", headers={"Origin": origin}).status_code == 401

    client.cookies.set(google_signin.FLOW_COOKIE, params["state"], domain="game.example")
    response = client.get(callback, params=params, follow_redirects=False)
    assert response.headers["location"].endswith("/#/google-error")
    assert len(requests_seen) == 1

    identity = ("unrelated-subject", "nova.agent@example.com")
    query = begin()
    response = client.get(callback, params={"state": query["state"][0], "code": "temporary"}, follow_redirects=False)
    assert response.headers["location"].endswith("/#/google-error")


def test_snapshot_restores_game_database(seeded_session, tmp_path):
    source = Path(seeded_session.bind.url.database)
    backup = tmp_path / "backed-up.db"
    restored = tmp_path / "restored.db"
    copy_database(source, backup)
    copy_database(backup, restored)
    with closing(sqlite3.connect(restored)) as db:
        assert db.execute("SELECT COUNT(*) FROM missions").fetchone() == (5,)
    with pytest.raises(FileExistsError):
        copy_database(backup, restored)


def test_catalog_only_seed_does_not_create_demo_accounts(tmp_path):
    from sqlalchemy.orm import Session
    from database import Base
    from models import Mission
    from seed import seed
    from tests.db_utils import make_engine

    engine = make_engine(tmp_path / "production.db")
    try:
        Base.metadata.create_all(bind=engine)
        with Session(engine) as db:
            seed(db, demo=False)
            assert db.query(User).count() == 0
            assert db.query(Mission).count() == 5
    finally:
        engine.dispose()


def test_password_recovery_uses_one_ticket_and_revokes_sessions(client, monkeypatch):
    import recovery
    from cryptography.fernet import Fernet

    for name in ("SMTP_HOST", "SMTP_FROM", "SMTP_USER", "SMTP_PASSWORD"):
        monkeypatch.setenv(name, "test-value")
    monkeypatch.setenv("CYBERHEIST_PUBLIC_ORIGIN", "https://game.example")
    monkeypatch.setenv("CYBERHEIST_MFA_KEYS", Fernet.generate_key().decode())
    mail = []
    monkeypatch.setattr(recovery, "send_reset", lambda email, token, config: mail.append((email, token)))
    credentials = {"username": "nova.agent", "password": "dev-only-nova"}
    session = client.post("/api/auth/login", json=credentials).json()
    headers = {"Authorization": "Bearer " + session["access_token"]}
    assert client.post("/api/auth/mfa/start", headers=headers,
                       json={"password": credentials["password"]}).status_code == 200
    request = "/api/auth/recovery/request"
    eligible = client.post(request, json={"email": "NOVA.AGENT@example.com"})
    absent = client.post(request, json={"email": "absent@example.com"})
    repeated = client.post(request, json={"email": "nova.agent@example.com"})
    assert eligible.status_code == absent.status_code == repeated.status_code == 202
    assert eligible.json() == absent.json() == repeated.json()
    assert len(mail) == 1
    assert mail[0][0] == "nova.agent@example.com"

    new_password = "replacement-passphrase"
    body = {"token": mail[0][1], "password": new_password}
    complete = "/api/auth/recovery/complete"
    assert client.post(complete, json=body).status_code == 204
    assert client.post(complete, json=body).status_code == 400
    assert client.post("/api/auth/login", json=credentials).status_code == 401
    credentials["password"] = new_password
    login = client.post("/api/auth/login", json=credentials)
    assert login.status_code == 200
    assert client.get("/api/me", headers=headers).status_code == 401
    new_token = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert client.post("/api/auth/mfa/confirm", headers=new_token, json={"code": "123456"}).status_code == 409


def test_optional_mfa_encrypted_setup_rejects_replay_and_uses_backup_once(client, seeded_session, monkeypatch):
    from types import SimpleNamespace

    import pyotp
    from cryptography.fernet import Fernet

    import mfa
    from models import AccountMfa

    monkeypatch.setenv("CYBERHEIST_MFA_KEYS", Fernet.generate_key().decode())
    step = 60_000_000
    monkeypatch.setattr(mfa, "time", SimpleNamespace(time=lambda: step * 30))

    login = "/api/auth/login"
    account = {"username": "nova.agent", "password": "dev-only-nova"}
    token = client.post(login, json=account).json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    root = "/api/auth/mfa"
    assert client.get(root, headers=headers).json() == {"available": True, "enabled": False}
    setup = client.post(root + "/start", headers=headers, json={"password": account["password"]})
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    totp = pyotp.TOTP(secret)
    seed_code = totp.generate_otp(step)
    confirm = client.post(root + "/confirm", headers=headers, json={"code": seed_code})
    assert confirm.status_code == 200
    recovery_codes = confirm.json()["recovery_codes"]
    factor = seeded_session.get(AccountMfa, 1)
    assert factor.secret != secret
    assert recovery_codes[0] not in factor.recovery_hashes
    assert client.post(login, json=account).status_code == 401
    assert client.post(login, json={**account, "mfa_code": seed_code}).status_code == 401

    step += 1
    next_code = totp.generate_otp(step)
    assert client.post(login, json={**account, "mfa_code": next_code}).status_code == 200
    assert client.post(login, json={**account, "mfa_code": next_code}).status_code == 401
    assert client.post(login, json={**account, "mfa_code": recovery_codes[0]}).status_code == 200
    assert client.post(login, json={**account, "mfa_code": recovery_codes[0]}).status_code == 401
    assert client.post(root + "/disable", headers=headers, json={
        "password": account["password"], "code": recovery_codes[1],
    }).status_code == 204
    assert client.post(login, json=account).status_code == 200
