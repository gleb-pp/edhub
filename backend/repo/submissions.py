from sqlalchemy import Integer, DateTime, Text, CheckConstraint, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from repo.base import Base


class AssignmentSubmission(Base):
    __tablename__ = "course_assignments_submissions"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True
    )
    assignment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True
    )
    timeadded: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(tz=timezone.utc))
    timemodified: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(tz=timezone.utc))
    submission_text: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["course_id", "assignment_id"],
            ["course_assignments.course_id", "course_assignments.assignment_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("timemodified >= timeadded"),
        CheckConstraint("length(submissiontext) BETWEEN 3 AND 10000"),
    )
