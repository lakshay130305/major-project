"""Application configuration — fully environment-driven, safe defaults for dev.

Nothing security-sensitive is hardcoded. In production (ENVIRONMENT=production)
the app refuses to start unless a strong SECRET_KEY is provided.
"""
from __future__ import annotations

import secrets
import warnings

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # ---- environment ----
    ENVIRONMENT: str = "development"  # development | production
    PROJECT_NAME: str = "Smart Tourist Safety Monitoring & Incident Response System"
    API_V1_PREFIX: str = "/api"

    # ---- database ----
    # SQLite for dev; set DATABASE_URL=postgresql+psycopg://user:pass@host/db in prod
    DATABASE_URL: str = "sqlite:///./tourist_safety.db"

    # ---- auth / JWT ----
    # Leave empty to auto-generate an ephemeral key in dev (tokens reset on restart).
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12h

    # ---- password policy ----
    MIN_PASSWORD_LENGTH: int = 8

    # ---- rate limiting (per client IP) ----
    RATE_LIMIT_ENABLED: bool = True
    LOGIN_RATE_LIMIT: int = 10          # attempts
    LOGIN_RATE_WINDOW_SECONDS: int = 300
    GLOBAL_RATE_LIMIT: int = 240        # requests
    GLOBAL_RATE_WINDOW_SECONDS: int = 60

    # ---- request hardening ----
    MAX_REQUEST_BODY_BYTES: int = 1_000_000  # 1 MB

    # ---- ML ----
    ML_MODELS_DIR: str = "ml_models"

    # ---- domain thresholds ----
    ROUTE_DEVIATION_THRESHOLD_M: float = 2000.0
    ANOMALY_INCIDENT_DEDUPE_MINUTES: int = 5

    # ---- map defaults (surfaced to the frontend via /api/config) ----
    MAP_CENTER_LAT: float = 26.1445
    MAP_CENTER_LNG: float = 91.7362
    MAP_DEFAULT_ZOOM: int = 13

    # ---- CORS / hosts (comma-separated in env) ----
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    ALLOWED_HOSTS: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @field_validator("ENVIRONMENT")
    @classmethod
    def _valid_env(cls, v: str) -> str:
        if v.lower() not in ("development", "production", "test"):
            raise ValueError("ENVIRONMENT must be development, production or test")
        return v.lower()

    @model_validator(mode="after")
    def _finalize_secret(self) -> "Settings":
        if not self.SECRET_KEY:
            if self.is_production:
                raise RuntimeError(
                    "SECRET_KEY must be set in production. Generate one with: "
                    "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
                )
            # dev convenience: ephemeral key
            self.SECRET_KEY = secrets.token_urlsafe(48)
            warnings.warn(
                "No SECRET_KEY set — using an ephemeral dev key (tokens reset on restart).",
                stacklevel=2,
            )
        elif len(self.SECRET_KEY) < 32 and self.is_production:
            raise RuntimeError("SECRET_KEY is too short for production (need >= 32 chars).")

        if self.is_production and "*" in self.allowed_hosts_list:
            warnings.warn("ALLOWED_HOSTS='*' in production is insecure — set explicit hosts.",
                          stacklevel=2)
        return self


settings = Settings()
