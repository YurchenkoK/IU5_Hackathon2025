from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager

from .config import settings


engine = create_engine(settings.database_url, echo=True, pool_pre_ping=True)


def init_db() -> None:
    """Initialize database schema"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


@contextmanager
def get_sync_session():
    """Get synchronous database session"""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
