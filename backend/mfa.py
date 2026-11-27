"""Encrypted TOTP enrollment, replay protection, and one-time backup codes."""

import hashlib
import os
import re
import secrets
import time
from datetime import timedelta

import pyotp
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from fastapi import HTTPException

from models import utc_now

SETUP_LIFETIME = timedelta(minutes=10)


def mfa_encryption():
    keys = os.getenv("CYBERHEIST_MFA_KEYS", "")
    if not keys:
        return None
    return MultiFernet([Fernet(key.strip().encode("ascii")) for key in keys.split(",")])


def encrypt_secret(secret):
    cipher = mfa_encryption()
    if cipher is None:
        raise HTTPException(503, "Authenticator setup is unavailable")
    return cipher.encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_secret(encrypted):
    try:
        cipher = mfa_encryption()
        if cipher is not None:
            return cipher.decrypt(encrypted.encode("ascii")).decode("ascii")
    except (ValueError, InvalidToken):
        pass
    raise HTTPException(503, "Authenticator verification is unavailable")


def matching_step(secret, code, last_step):
    if not re.fullmatch(r"[0-9]{6}", code):
        return None
    totp = pyotp.TOTP(secret)
    current_step = int(time.time()) // totp.interval
    for step in (current_step, current_step - 1, current_step + 1):
        if step > last_step and secrets.compare_digest(code, totp.generate_otp(step)):
            return step
    return None


def recovery_digest(code):
    return hashlib.sha256(code.encode()).hexdigest()


def check_attempt_budget(factor):
    now = utc_now()
    if factor.blocked_until and factor.blocked_until > now:
        raise HTTPException(429, "Too many authenticator attempts. Try again in five minutes.")
    if factor.blocked_until:
        factor.failures = 0
        factor.blocked_until = None


def record_failure(db, factor):
    factor.failures += 1
    if factor.failures >= 5:
        factor.blocked_until = utc_now() + timedelta(minutes=5)
    db.commit()


def accept_factor(db, factor, code, *, failure_status=401):
    if not factor or not factor.secret:
        return
    if not code:
        raise HTTPException(failure_status, "Enter your authenticator or backup code")
    check_attempt_budget(factor)
    code = code.strip()
    step = matching_step(decrypt_secret(factor.secret), code, factor.last_step)
    digest = recovery_digest(code)
    backup = next((value for value in factor.recovery_hashes
                   if secrets.compare_digest(digest, value)), None)
    if step is not None:
        factor.last_step = step
    elif backup:
        factor.recovery_hashes = [value for value in factor.recovery_hashes if value != backup]
    else:
        record_failure(db, factor)
        raise HTTPException(failure_status, "Invalid authenticator or backup code")
    factor.failures = 0
