from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from omics_registry.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, echo=settings.echo_sql, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def session_scope():
    """Context manager for scripts/CLI commands (outside a FastAPI request).

    Commits on success, rolls back on any exception, always closes.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
