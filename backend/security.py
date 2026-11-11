"""Hashing helpers for demo accounts and puzzle answers.

Passwords use PBKDF2-HMAC-SHA256. The stored format is:

    pbkdf2_sha256$<iterations>$<salt>$<hex digest>

Demo seed data uses a fixed salt per username so the Python seed and
database/seed.sql stay the same from run to run. That is only acceptable for
local development. A future registration route should pass salt=None so each
password gets its own random salt. The format above already supports that.

Puzzle answers are stored as the SHA-256 hex digest of the stripped,
case-folded answer. The plaintext answer is not a database column.
"""

import hashlib
import secrets

PBKDF2_ITERATIONS = 260_000


def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
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


def hash_solution(answer: str) -> str:
    """Return the SHA-256 hex digest of a normalized puzzle answer."""
    normalized = answer.strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
