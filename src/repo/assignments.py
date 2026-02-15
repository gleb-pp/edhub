from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.repo.base import Base
from src.settings.assignments import assignment_settings


class CourseAssignment(Base):
    __tablename__ = "course_assignments"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True,
    )
    assignment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
    )
    creation_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=UTC),
    )
    author: Mapped[str | None] = mapped_column(
        ForeignKey("users.email", ondelete="SET NULL"), nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    section_id: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["course_id", "section_id"],
            ["course_sections.course_id", "course_sections.section_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            f"length(title) BETWEEN {assignment_settings.name_min_lenght} AND {assignment_settings.name_max_lenght}",
        ),
        CheckConstraint(
            f"length(description) BETWEEN {assignment_settings.description_min_lenght} AND {assignment_settings.description_max_lenght}",
        ),
    )
