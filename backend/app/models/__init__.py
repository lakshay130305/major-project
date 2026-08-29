"""Import all models so SQLAlchemy's metadata registers them."""
from app.models.alert import Alert
from app.models.audit import AuditLog
from app.models.incident import Incident, IncidentEvent
from app.models.police import PoliceUnit
from app.models.tourist import IdBlock, LocationPing, Tourist
from app.models.user import User
from app.models.zone import Zone

__all__ = [
    "User",
    "Tourist",
    "IdBlock",
    "LocationPing",
    "Zone",
    "Incident",
    "IncidentEvent",
    "Alert",
    "PoliceUnit",
    "AuditLog",
]
