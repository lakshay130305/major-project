from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.api.deps import authenticate_ws_token
from app.db.session import SessionLocal
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/alerts")
async def alerts_ws(ws: WebSocket, token: str | None = Query(default=None)):
    """Live alert/incident/location feed. Requires a valid admin token because the
    stream contains tourist locations and PII."""
    db = SessionLocal()
    try:
        user = authenticate_ws_token(token, db)
    finally:
        db.close()

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
