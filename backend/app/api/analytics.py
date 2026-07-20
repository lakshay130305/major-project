from collections import Counter, defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.tourist import Tourist
from app.models.user import User
from app.models.zone import Zone

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    tourists = db.query(Tourist).all()
    incidents = db.query(Incident).all()
    active_alerts = db.query(Alert).filter(Alert.acknowledged == False).count()  # noqa: E712

    resolved = [i for i in incidents if i.response_time_seconds is not None]
    avg_response = (
        sum(i.response_time_seconds for i in resolved) / len(resolved) if resolved else 0
    )
    return {
        "total_tourists": len(tourists),
        "active_tourists": sum(1 for t in tourists if t.status == "active"),
        "sos_active": sum(1 for t in tourists if t.status == "sos"),
        "missing": sum(1 for t in tourists if t.status == "missing"),
        "total_incidents": len(incidents),
        "open_incidents": sum(1 for i in incidents if i.status != "resolved"),
        "active_alerts": active_alerts,
        "avg_safety_score": round(
            sum(t.safety_score for t in tourists) / len(tourists), 1
        ) if tourists else 0,
        "avg_response_time_seconds": round(avg_response, 1),
        "total_zones": db.query(Zone).count(),
    }


@router.get("/alerts-by-type")
def alerts_by_type(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    counts = Counter(a.type for a in db.query(Alert).all())
    return [{"type": k, "count": v} for k, v in counts.items()]


@router.get("/incidents-over-time")
def incidents_over_time(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    by_day: dict[str, int] = defaultdict(int)
    for i in db.query(Incident).all():
        by_day[i.detected_at.strftime("%Y-%m-%d")] += 1
    return [{"date": d, "count": c} for d, c in sorted(by_day.items())]


@router.get("/zone-risk")
def zone_risk(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    zones = db.query(Zone).all()
    alerts = db.query(Alert).filter(Alert.type == "geofence").all()
    # rough attribution: geofence alert counts per zone by name mention
    counts: dict[str, int] = defaultdict(int)
    for a in alerts:
        for z in zones:
            if z.name in (a.message or ""):
                counts[z.name] += 1
    return [
        {"zone": z.name, "risk_level": z.risk_level, "crime_index": z.crime_index,
         "alert_count": counts.get(z.name, 0)}
        for z in zones
    ]


@router.get("/severity-breakdown")
def severity_breakdown(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    counts = Counter(i.severity for i in db.query(Incident).all())
    return [{"severity": k, "count": v} for k, v in counts.items()]
