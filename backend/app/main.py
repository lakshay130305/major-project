"""FastAPI application entrypoint for the Smart Tourist Safety system."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, incidents, tourists, ws, zones
from app.core.config import settings
from app.db.session import init_db

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "healthy"}


PREFIX = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=PREFIX)
app.include_router(tourists.router, prefix=PREFIX)
app.include_router(zones.router, prefix=PREFIX)
app.include_router(incidents.router, prefix=PREFIX)
app.include_router(analytics.router, prefix=PREFIX)
app.include_router(ws.router)  # websocket at /ws/alerts
