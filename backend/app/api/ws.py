from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.api.deps import authenticate_ws_token
from app.db.session import get_db
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/alerts")
async def alerts_ws(ws: WebSocket, token: str | None = Query(default=None),
                    db: Session = Depends(get_db)):
    """Live alert/incident/location feed. Requires a valid admin token because the
    stream contains tourist locations and PII.

    The session comes from the standard `get_db` dependency rather than calling
    SessionLocal() directly, so dependency overrides apply here as they do to the
    REST routes.
    """
    user = authenticate_ws_token(token, db)

    if user is None or user.role != "admin":
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(ws)
    try:
        await ws.send_json({"event": "connected", "message": "live feed established"})
        while True:
            # keep the socket open; ignore inbound (client is a listener)
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)
    except Exception:
        await manager.disconnect(ws)
