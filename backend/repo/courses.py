from sqlalchemy import DateTime, Text, CheckConstraint, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4
from datetime import datetime, timezone

from repo.base import Base


class Course(Base):
    """Database model for the courses."""

    __tablename__ = "courses"
    
    course_id: Mapped[str] = mapped_column(Uuid, primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    organization: Mapped[str | None] = mapped_column(Text)
    instructor: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), nullable=False
    )
    creation_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(tz=timezone.utc))

    __table_args__ = (
        CheckConstraint("length(title) BETWEEN 3 AND 80"),
        CheckConstraint("organization IS NULL OR length(organization) BETWEEN 3 AND 80"),
    )
