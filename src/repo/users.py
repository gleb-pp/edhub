from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.repo.base import Base


class User(Base):
    """Database model for the users."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(254), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    time_registered: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=UTC),
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
