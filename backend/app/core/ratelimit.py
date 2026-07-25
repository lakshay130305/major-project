"""Lightweight in-memory sliding-window rate limiter (per client IP).

No external dependency. Suitable for a single-instance deployment or academic
demo. For horizontally-scaled production, back this with Redis instead.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import settings

_lock = threading.Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # Honour a single proxy hop if present (X-Forwarded-For), else peer address.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check(key: str, limit: int, window: int) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    now = time.monotonic()
    with _lock:
        dq = _hits[key]
        cutoff = now - window
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= limit:
            retry = int(dq[0] + window - now) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests — please slow down.",
                headers={"Retry-After": str(retry)},
            )
        dq.append(now)


def global_rate_limit(request: Request) -> None:
    """FastAPI dependency: coarse per-IP limit across the whole API."""
    _check(
        f"global:{_client_ip(request)}",
        settings.GLOBAL_RATE_LIMIT,
        settings.GLOBAL_RATE_WINDOW_SECONDS,
    )


def login_rate_limit(request: Request) -> None:
    """Stricter limit for the login endpoint (brute-force protection)."""
    _check(
        f"login:{_client_ip(request)}",
        settings.LOGIN_RATE_LIMIT,
        settings.LOGIN_RATE_WINDOW_SECONDS,
    )
