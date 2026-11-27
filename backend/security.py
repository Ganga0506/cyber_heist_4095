"""Argon2id passwords with PBKDF2 verification for existing accounts."""

import hashlib
import os
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

PBKDF2_ITERATIONS = 260_000
PASSWORD_HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
DUMMY_PASSWORD_HASH = PASSWORD_HASHER.hash(secrets.token_urlsafe())


def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        return PASSWORD_HASHER.hash(password)
    # Explicit salts are used by the deterministic demo SQL generator.
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith("$argon2id$"):
        try:
            return PASSWORD_HASHER.verify(stored_hash, password)
        except (VerificationError, InvalidHashError):
            return False
    try:
        algorithm, iterations, salt, digest = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        check = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
    except (ValueError, TypeError):
        return False
    return secrets.compare_digest(check, digest)


def password_needs_rehash(stored_hash: str) -> bool:
    return not stored_hash.startswith("$argon2id$") or PASSWORD_HASHER.check_needs_rehash(stored_hash)


def breached_password(password: str) -> bool:
    """Look up a SHA-1 digest in a read-only breached-password corpus."""
    corpus = os.getenv("CYBERHEIST_BREACHED_PASSWORD_DB")
    if not corpus:
        if os.getenv("CYBERHEIST_ENV") == "production":
            raise RuntimeError("Production requires a breached-password corpus")
        return False
    digest = hashlib.sha1(password.encode("utf-8"), usedforsecurity=False).hexdigest().upper()
    with closing(sqlite3.connect(Path(corpus).resolve().as_uri() + "?mode=ro", uri=True)) as db:
        return db.execute("SELECT 1 FROM breached_passwords WHERE digest = ?", (digest,)).fetchone() is not None


def hash_solution(answer: str) -> str:
    """Return the SHA-256 hex digest of a normalized puzzle answer."""
    normalized = answer.strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
