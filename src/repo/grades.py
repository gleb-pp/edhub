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


class Grade(Base):
    """SQLAlchemy model for grades assigned to student submissions."""

    __tablename__ = "grades"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True,
    )
    assignment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True,
    )
    grade: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    teacher_email: Mapped[str | None] = mapped_column(
        ForeignKey("users.email", ondelete="SET NULL"), nullable=True,
    )
    time_graded: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=UTC),
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["course_id", "assignment_id", "student_email"],
            [
                "course_assignments_submissions.course_id",
                "course_assignments_submissions.assignment_id",
                "course_assignments_submissions.email",
            ],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            f"comment IS NULL OR length(comment) BETWEEN {submission_settings.grade_comment_min_length} AND {submission_settings.grade_comment_max_length}",
        ),
    )
