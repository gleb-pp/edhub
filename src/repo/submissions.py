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
from src.settings.submissions import submission_settings


class AssignmentSubmission(Base):
    """SQLAlchemy model for student submissions to course assignments."""

    __tablename__ = "course_assignments_submissions"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True,
    )
    assignment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True,
    )
    timeadded: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=UTC),
    )
    timemodified: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=UTC),
    )
    submission_text: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["course_id", "assignment_id"],
            ["course_assignments.course_id", "course_assignments.assignment_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["email", "course_id"],
            ["student_at.email", "student_at.course_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("timemodified >= timeadded"),
        CheckConstraint(
            f"length(submission_text) BETWEEN {submission_settings.text_min_length} AND {submission_settings.text_max_length}",
        ),
    )
