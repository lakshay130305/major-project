from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.alert import Alert
from app.models.incident import Incident, IncidentEvent
from app.models.police import PoliceUnit
from app.models.tourist import Tourist
from app.models.user import User
from app.schemas.incident import (
    AlertOut,
    IncidentOut,
    IncidentStatusUpdate,
    PoliceUnitOut,
    SOSRequest,
)
from app.services.efir import generate_efir
from app.services.monitoring import trigger_sos

router = APIRouter(tags=["incidents"])

_NEXT = {"detected": "acknowledged", "acknowledged": "dispatched", "dispatched": "resolved"}


# ---------------- alerts ----------------
@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(limit: int = 100, only_active: bool = False,
                db: Session = Depends(get_db), _: User = Depends(require_admin)):
    q = db.query(Alert)
    if only_active:
        q = q.filter(Alert.acknowledged == False)  # noqa: E712
    return q.order_by(Alert.created_at.desc()).limit(limit).all()


@router.post("/alerts/{alert_id}/ack")
def ack_alert(alert_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    a.acknowledged = True
    db.commit()
    return {"id": alert_id, "acknowledged": True}


# ---------------- SOS ----------------
@router.post("/tourists/{tourist_id}/sos")
def sos(tourist_id: int, payload: SOSRequest, db: Session = Depends(get_db),
        user: User = Depends(get_current_user)):
    t = db.get(Tourist, tourist_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tourist not found")
    return trigger_sos(db, t, payload.lat, payload.lng, payload.message)


# ---------------- incidents ----------------
@router.get("/incidents", response_model=list[IncidentOut])
def list_incidents(status: str | None = None, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    q = db.query(Incident)
    if status:
        q = q.filter(Incident.status == status)
    return q.order_by(Incident.detected_at.desc()).all()


@router.get("/incidents/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db),
                 _: User = Depends(require_admin)):
    inc = db.get(Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@router.patch("/incidents/{incident_id}", response_model=IncidentOut)
def update_incident(incident_id: int, payload: IncidentStatusUpdate,
                    db: Session = Depends(get_db), _: User = Depends(require_admin)):
    inc = db.get(Incident, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    inc.status = payload.status
    if payload.status == "acknowledged":
        inc.acknowledged_at = now
    elif payload.status == "dispatched":
        inc.dispatched_at = now
    elif payload.status == "resolved":
        inc.resolved_at = now
        if inc.tourist_id:
            t = db.get(Tourist, inc.tourist_id)
            if t and t.status == "sos":
                t.status = "active"
    db.add(IncidentEvent(incident_id=inc.id, status=payload.status, note=payload.note))
    db.commit()
    db.refresh(inc)
    return inc


@router.get("/incidents/{incident_id}/efir")
def incident_efir(incident_id: int, db: Session = Depends(get_db),
                  _: User = Depends(require_admin)):
    inc = db.get(Incident, incident_id)
    if not inc or not inc.tourist_id:
        raise HTTPException(status_code=404, detail="Incident/tourist not found")
    t = db.get(Tourist, inc.tourist_id)
    return generate_efir(db, t)


@router.post("/tourists/{tourist_id}/mark-missing")
def mark_missing(tourist_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    t = db.get(Tourist, tourist_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tourist not found")
    t.status = "missing"
    inc = Incident(tourist_id=t.id, type="missing_person", severity="critical",
                   status="detected", description=f"{t.full_name} reported missing",
                   lat=t.last_lat, lng=t.last_lng)
    db.add(inc)
    db.flush()
    db.add(IncidentEvent(incident_id=inc.id, status="detected", note="Marked missing"))
    db.commit()
    return {"tourist_id": tourist_id, "status": "missing", "incident_id": inc.id,
            "efir": generate_efir(db, t)}


# ---------------- police units ----------------
@router.get("/police-units", response_model=list[PoliceUnitOut])
def list_units(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(PoliceUnit).all()
