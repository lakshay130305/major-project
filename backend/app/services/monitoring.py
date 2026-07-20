"""Core pipeline: ingest a location ping -> anomaly + geofence checks ->
alerts, incidents, safety-score refresh, and WebSocket broadcast."""
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alert
from app.models.incident import Incident, IncidentEvent
from app.models.tourist import LocationPing, Tourist
from app.models.zone import Zone
from app.services import ml_service
from app.services.geo import (
    haversine_m,
    min_distance_to_route,
    zones_containing_point,
)
from app.services.safety import compute_safety_score
from app.websocket.manager import broadcast_sync

_RISK_SEVERITY = {"low": "low", "medium": "medium", "high": "high", "restricted": "critical"}


def _create_alert(db: Session, tourist_id, atype, severity, message, lat, lng) -> Alert:
    alert = Alert(
        tourist_id=tourist_id, type=atype, severity=severity,
        message=message, lat=lat, lng=lng,
    )
    db.add(alert)
    db.flush()
    broadcast_sync({
        "event": "alert",
        "id": alert.id,
        "tourist_id": tourist_id,
        "type": atype,
        "severity": severity,
        "message": message,
        "lat": lat, "lng": lng,
        "created_at": alert.created_at.isoformat(),
    })
    return alert


def _open_incident(db: Session, tourist: Tourist, itype, severity, description, lat, lng) -> Incident:
    inc = Incident(
        tourist_id=tourist.id, type=itype, severity=severity,
        status="detected", description=description, lat=lat, lng=lng,
    )
    db.add(inc)
    db.flush()
    db.add(IncidentEvent(incident_id=inc.id, status="detected", note=description))
    db.flush()
    broadcast_sync({
        "event": "incident",
        "id": inc.id,
        "tourist_id": tourist.id,
        "type": itype,
        "severity": severity,
        "status": "detected",
        "lat": lat, "lng": lng,
    })
    return inc


def process_ping(db: Session, tourist: Tourist, lat: float, lng: float,
                 speed_kmh: float = 0.0) -> dict:
    """Process one GPS ping. Returns a summary dict for the caller/API."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # distance/time from previous ping
    prev = (
        db.query(LocationPing)
        .filter(LocationPing.tourist_id == tourist.id)
        .order_by(LocationPing.timestamp.desc())
        .first()
    )
    if prev:
        dist_prev = haversine_m(prev.lat, prev.lng, lat, lng)
        dt = max((now - prev.timestamp).total_seconds(), 1.0)
    else:
        dist_prev, dt = 0.0, 1.0

    itinerary = json.loads(tourist.itinerary or "[]")
    dist_route = min_distance_to_route(lat, lng, itinerary)

    # ---- anomaly detection (IsolationForest) ----
    feats = ml_service.anomaly_features(speed_kmh, dist_prev, dt, dist_route)
    anomaly = ml_service.score_anomaly(feats)

    ping = LocationPing(
        tourist_id=tourist.id, lat=lat, lng=lng, speed_kmh=speed_kmh,
        timestamp=now, anomaly_score=anomaly["score"], is_anomaly=anomaly["is_anomaly"],
    )
    db.add(ping)

    tourist.last_lat, tourist.last_lng, tourist.last_seen = lat, lng, now

    alerts_raised = []

    if anomaly["is_anomaly"]:
        reason = "unusual movement pattern"
        if speed_kmh > 120:
            reason = f"abnormal speed {speed_kmh:.0f} km/h (possible vehicle abduction)"
        elif dt / 60.0 > 45:
            reason = f"prolonged inactivity {dt/60:.0f} min"
        elif dist_prev > 5000:
            reason = f"sudden location jump {dist_prev/1000:.1f} km"
        a = _create_alert(db, tourist.id, "anomaly", "high",
                          f"Anomaly detected: {reason}", lat, lng)
        alerts_raised.append("anomaly")
        # De-dupe: only open a new incident if there isn't already an unresolved
        # anomaly incident for this tourist in the last 5 minutes (avoids flooding
        # the incident feed when the tourist stays anomalous across many pings).
        recent = (
            db.query(Incident)
            .filter(
                Incident.tourist_id == tourist.id,
                Incident.type == "anomaly",
                Incident.status != "resolved",
                Incident.detected_at >= now - timedelta(minutes=5),
            )
            .first()
        )
        if not recent:
            _open_incident(db, tourist, "anomaly", "high",
                           f"AI anomaly: {reason}", lat, lng)

    # ---- route deviation ----
    if itinerary and dist_route > settings.ROUTE_DEVIATION_THRESHOLD_M:
        _create_alert(db, tourist.id, "route_deviation", "medium",
                      f"Route deviation: {dist_route/1000:.1f} km from planned itinerary",
                      lat, lng)
        alerts_raised.append("route_deviation")

    # ---- geofence ----
    zones = db.query(Zone).all()
    inside = zones_containing_point(lat, lng, zones)
    risky = [z for z in inside if z.risk_level in ("high", "restricted")]
    for z in risky:
        sev = _RISK_SEVERITY.get(z.risk_level, "medium")
        _create_alert(db, tourist.id, "geofence", sev,
                      f"Entered {z.risk_level} risk zone: {z.name}", lat, lng)
        alerts_raised.append("geofence")

    # ---- safety score refresh ----
    ss = compute_safety_score(db, tourist, anomaly_score=anomaly["score"])
    tourist.safety_score = ss["score"]

    db.commit()
    broadcast_sync({
        "event": "location",
        "tourist_id": tourist.id,
        "digital_id": tourist.digital_id,
        "lat": lat, "lng": lng,
        "safety_score": ss["score"],
        "status": tourist.status,
    })

    return {
        "tourist_id": tourist.id,
        "anomaly": anomaly,
        "route_deviation_m": round(dist_route, 1),
        "in_zones": [z.name for z in inside],
        "alerts_raised": alerts_raised,
        "safety_score": ss["score"],
        "band": ss["band"],
    }


def trigger_sos(db: Session, tourist: Tourist, lat: float, lng: float, message: str) -> dict:
    """One-tap SOS: mark tourist, find nearest available police unit, open critical incident."""
    from app.models.police import PoliceUnit

    tourist.status = "sos"
    tourist.last_lat, tourist.last_lng = lat, lng
    tourist.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)

    units = db.query(PoliceUnit).filter(PoliceUnit.available == True).all()  # noqa: E712
    nearest = min(units, key=lambda u: haversine_m(lat, lng, u.lat, u.lng), default=None)

    inc = _open_incident(db, tourist, "sos", "critical",
                         f"SOS triggered by {tourist.full_name}: {message}", lat, lng)
    if nearest:
        inc.assigned_unit_id = nearest.id
        inc.status = "dispatched"
        inc.dispatched_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add(IncidentEvent(incident_id=inc.id, status="dispatched",
                             note=f"Auto-dispatched to {nearest.name} ({nearest.station})"))

    _create_alert(db, tourist.id, "sos", "critical",
                  f"🚨 SOS from {tourist.full_name}", lat, lng)

    contacts = json.loads(tourist.emergency_contacts or "[]")
    db.commit()

    return {
        "incident_id": inc.id,
        "nearest_unit": {
            "name": nearest.name, "station": nearest.station,
            "phone": nearest.phone, "lat": nearest.lat, "lng": nearest.lng,
            "distance_km": round(haversine_m(lat, lng, nearest.lat, nearest.lng) / 1000, 2),
        } if nearest else None,
        "notified_contacts": contacts,
    }
