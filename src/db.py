import contextlib
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.auth import hash_password
from src.repo.base import Base
from src.repo.users import User
from src.settings.admins import admin_settings

DATABASE_URL = "postgresql+psycopg://postgres:12345678@system_db:5432/edhub"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create database tables based on the defined models."""
    Base.metadata.create_all(bind=engine)


def create_default_admin_account() -> None:
    """Create the default admin account."""
    db_gen = get_db()
    db = next(db_gen)
    try:
        if (
            db.query(User)
            .filter(User.email == admin_settings.default_account_email)
            .first()
            is not None
        ):
            print("Default admin account exists, skipping...")
            return
        hashed_password = hash_password(admin_settings.default_account_password)
        user = User(
            email=admin_settings.default_account_email,
            name=admin_settings.default_account_name,
            password_hash=hashed_password,
            is_admin=True,
        )
        db.add(user)
        db.commit()
        print("Default admin account created!")
    except Exception as e:
        db.rollback()
        print(f"Error while creating the default admin account: {e}")
        raise
    finally:
        with contextlib.suppress(StopIteration):
            next(db_gen)


def get_db() -> Generator[Session, None, None]:
    """Session generator for database operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
