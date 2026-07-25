"""Security audit trail for sensitive actions (logins, SOS, admin changes)."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    actor: Mapped[str] = mapped_column(String, default="anonymous")  # email or "system"
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
    target: Mapped[str] = mapped_column(String, default="")
    ip: Mapped[str] = mapped_column(String, default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    outcome: Mapped[str] = mapped_column(String, default="success")  # success / failure
