from datetime import datetime

from pydantic import BaseModel, Field


class Waypoint(BaseModel):
    name: str
    lat: float
    lng: float


class EmergencyContact(BaseModel):
    name: str
    phone: str
    relation: str = "family"


class TouristCreate(BaseModel):
    full_name: str
    nationality: str = "Indian"
    document_type: str = "aadhaar"
    document_number: str
    phone: str
    itinerary: list[Waypoint] = Field(default_factory=list)
    emergency_contacts: list[EmergencyContact] = Field(default_factory=list)
    trip_start: datetime
    trip_end: datetime
    # optional login creds; if provided a tourist user account is created
    password: str | None = None
    email: str | None = None


class TouristOut(BaseModel):
    id: int
    digital_id: str
    full_name: str
    nationality: str
    document_type: str
    document_number: str
    phone: str
    itinerary: list[Waypoint]
    emergency_contacts: list[EmergencyContact]
    trip_start: datetime
    trip_end: datetime
    last_lat: float | None
    last_lng: float | None
    last_seen: datetime | None
    safety_score: float
    tracking_enabled: bool
    status: str
    is_valid: bool

    class Config:
        from_attributes = True


class LocationUpdate(BaseModel):
    lat: float
    lng: float
    speed_kmh: float = 0.0


class SafetyScoreOut(BaseModel):
    tourist_id: int
    score: float
    band: str
    breakdown: dict


class IdBlockOut(BaseModel):
    index: int
    timestamp: datetime
    event: str
    data: str
    previous_hash: str
    hash: str

    class Config:
        from_attributes = True
