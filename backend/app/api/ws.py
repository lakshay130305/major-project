from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/alerts")
async def alerts_ws(ws: WebSocket):
    """Dashboard subscribes here for live alert/incident/location events."""
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
