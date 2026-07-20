from datetime import datetime

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    tourist_id: int | None
    type: str
    severity: str
    message: str
    lat: float | None
    lng: float | None
    acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentEventOut(BaseModel):
    status: str
    note: str
    timestamp: datetime

    class Config:
        from_attributes = True


class IncidentOut(BaseModel):
    id: int
    tourist_id: int | None
    type: str
    severity: str
    status: str
    description: str
    lat: float | None
    lng: float | None
    assigned_unit_id: int | None
    detected_at: datetime
    acknowledged_at: datetime | None
    dispatched_at: datetime | None
    resolved_at: datetime | None
    response_time_seconds: float | None
    events: list[IncidentEventOut] = []

    class Config:
        from_attributes = True


class IncidentStatusUpdate(BaseModel):
    status: str  # acknowledged / dispatched / resolved
    note: str = ""


class SOSRequest(BaseModel):
    lat: float
    lng: float
    message: str = "SOS - emergency assistance required"


class PoliceUnitOut(BaseModel):
    id: int
    name: str
    station: str
    phone: str
    lat: float
    lng: float
    available: bool

    class Config:
        from_attributes = True
