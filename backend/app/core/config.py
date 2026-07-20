"""Application configuration loaded from environment / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Smart Tourist Safety Monitoring & Incident Response System"
    API_V1_PREFIX: str = "/api"

    # SQLite for dev; swap DATABASE_URL for PostgreSQL in prod
    DATABASE_URL: str = "sqlite:///./tourist_safety.db"

    # JWT
    SECRET_KEY: str = "CHANGE_ME_super_secret_dev_key_for_academic_project_only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # ML model artifact directory
    ML_MODELS_DIR: str = "ml_models"

    # Route deviation threshold in metres
    ROUTE_DEVIATION_THRESHOLD_M: float = 2000.0

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
