"""SQLAlchemy engine, session factory and declarative base."""
import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Verify the database schema is current.

    Schema changes are owned by Alembic (`alembic upgrade head`), not by
    `create_all`. create_all silently does nothing to an existing table, so a
    model change would appear to work locally and then fail in production
    against the older schema. This checks the applied revision and says plainly
    what to do instead of guessing.
    """
    from app import models  # noqa: F401  (ensures models are imported)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if not tables:
        logger.warning(
            "Database is empty. Run 'alembic upgrade head' to create the schema."
        )
        return

    if "alembic_version" not in tables:
        logger.warning(
            "Schema exists but is not under Alembic control. Run "
            "'alembic stamp head' to adopt it."
        )
        return

    with engine.connect() as conn:
        current = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    logger.info("Database schema at revision %s", current)
