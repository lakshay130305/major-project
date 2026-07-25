"""Helper to record audit-log entries. Never raises into the request path."""
from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def _ip(request: Request | None) -> str:
    if request is None:
        return ""
    fwd = request.headers.get("x-forwarded-for") if request else None
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request and request.client else ""


def record(db: Session, action: str, actor: str = "anonymous", target: str = "",
           detail: str = "", outcome: str = "success",
           request: Request | None = None) -> None:
    try:
        db.add(AuditLog(
            actor=actor, action=action, target=target,
            detail=detail, outcome=outcome, ip=_ip(request),
        ))
        db.commit()
    except Exception:  # noqa: BLE001 — auditing must never break the request
        db.rollback()
