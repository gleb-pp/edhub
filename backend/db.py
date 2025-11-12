from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from repo.base import Base

DATABASE_URL = "postgresql://postgres:12345678@system_db:5432/edhub"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create database tables based on the defined models."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Session generator for database operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
