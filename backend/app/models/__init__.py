"""Import all models so SQLAlchemy's metadata registers them."""
from app.models.user import User
from app.models.tourist import Tourist, IdBlock, LocationPing
from app.models.zone import Zone
from app.models.incident import Incident, IncidentEvent
from app.models.alert import Alert
from app.models.police import PoliceUnit

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
]
