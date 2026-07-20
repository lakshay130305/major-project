"""Tourist profile, tamper-proof digital ID hash-chain, and location pings."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Tourist(Base):
    __tablename__ = "tourists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    digital_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # KYC
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    nationality: Mapped[str] = mapped_column(String, default="Indian")
    document_type: Mapped[str] = mapped_column(String, default="aadhaar")  # aadhaar / passport
    document_number: Mapped[str] = mapped_column(String, nullable=False)  # mock/masked
    phone: Mapped[str] = mapped_column(String, nullable=False)

    # Trip
    itinerary: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of {name,lat,lng}
    emergency_contacts: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    trip_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    trip_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Live state
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    safety_score: Mapped[float] = mapped_column(Float, default=100.0)
    tracking_enabled: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String, default="active")  # active / sos / missing

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    id_blocks: Mapped[list["IdBlock"]] = relationship(
        back_populates="tourist", cascade="all, delete-orphan"
    )

    @property
    def is_valid(self) -> bool:
        """Digital ID validity is tied to trip duration."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return self.trip_start <= now <= self.trip_end


class IdBlock(Base):
    """A block in the tamper-proof SHA-256 hash chain for a tourist's ID record."""

    __tablename__ = "id_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tourist_id: Mapped[int] = mapped_column(ForeignKey("tourists.id"), index=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    event: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "ID_ISSUED"
    data: Mapped[str] = mapped_column(Text, default="{}")  # JSON payload
    previous_hash: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str] = mapped_column(String, nullable=False)

    tourist: Mapped["Tourist"] = relationship(back_populates="id_blocks")


class LocationPing(Base):
    """Historical GPS ping stream used by anomaly detection."""

    __tablename__ = "location_pings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tourist_id: Mapped[int] = mapped_column(ForeignKey("tourists.id"), index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    speed_kmh: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_anomaly: Mapped[bool] = mapped_column(default=False)
