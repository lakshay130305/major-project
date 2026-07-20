"""Auto-generate an E-FIR (First Information Report) draft for missing tourists."""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.tourist import Tourist


def generate_efir(db: Session, tourist: Tourist) -> dict:
    """Fill an E-FIR template from tourist KYC + last location + anomaly timeline."""
    contacts = json.loads(tourist.emergency_contacts or "[]")
    itinerary = json.loads(tourist.itinerary or "[]")

    anomaly_alerts = (
        db.query(Alert)
        .filter(Alert.tourist_id == tourist.id)
        .order_by(Alert.created_at.asc())
        .all()
    )
    timeline = [
        {
            "time": a.created_at.isoformat(),
            "type": a.type,
            "severity": a.severity,
            "message": a.message,
            "lat": a.lat,
            "lng": a.lng,
        }
        for a in anomaly_alerts
    ]

    now = datetime.utcnow()
    fir_no = f"EFIR/{now.year}/{tourist.id:05d}"

    narrative = (
        f"This E-FIR is auto-generated for missing person {tourist.full_name} "
        f"(Digital Tourist ID: {tourist.digital_id}, {tourist.document_type.upper()} "
        f"No: {tourist.document_number}). The tourist was last seen at coordinates "
        f"({tourist.last_lat}, {tourist.last_lng}) on "
        f"{tourist.last_seen.isoformat() if tourist.last_seen else 'unknown'}. "
        f"The Smart Tourist Safety system recorded {len(timeline)} anomaly/alert event(s) "
        f"prior to loss of contact. Immediate search and rescue is recommended."
    )

    return {
        "fir_number": fir_no,
        "generated_at": now.isoformat(),
        "status": "DRAFT",
        "subject": {
            "name": tourist.full_name,
            "nationality": tourist.nationality,
            "document_type": tourist.document_type,
            "document_number": tourist.document_number,
            "phone": tourist.phone,
            "digital_id": tourist.digital_id,
        },
        "trip": {
            "start": tourist.trip_start.isoformat(),
            "end": tourist.trip_end.isoformat(),
            "itinerary": itinerary,
        },
        "last_known_location": {
            "lat": tourist.last_lat,
            "lng": tourist.last_lng,
            "seen_at": tourist.last_seen.isoformat() if tourist.last_seen else None,
        },
        "emergency_contacts": contacts,
        "anomaly_timeline": timeline,
        "narrative": narrative,
    }
