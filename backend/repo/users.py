from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from repo.base import Base


class User(Base):
    """Database model for the users."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(254), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    isadmin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    timeregistered: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=timezone.utc)
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
