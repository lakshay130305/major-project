"""Password hashing, password policy, and JWT token helpers."""
from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ---------------------------------------------------------------- passwords
def hash_password(password: str) -> str:
    # bcrypt has a 72-byte input limit; truncate defensively.
    pw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def validate_password_strength(password: str) -> None:
    """Raise ValueError if the password is too weak. Kept simple & explainable."""
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters."
        )
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("Password must contain both letters and numbers.")


# ---------------------------------------------------------------- JWT
def create_access_token(subject: str, role: str, tourist_id: int | None = None,
                        expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "tid": tourist_id,
        "iat": now,
        "nbf": now,
        "exp": expire,
        "jti": secrets.token_urlsafe(16),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload
