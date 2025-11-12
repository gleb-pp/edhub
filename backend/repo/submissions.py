from sqlalchemy import Integer, DateTime, Text, CheckConstraint, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from repo.base import Base


class AssignmentSubmission(Base):
    __tablename__ = "course_assignments_submissions"

    courseid: Mapped[str] = mapped_column(
        ForeignKey("courses.courseid", ondelete="CASCADE"), primary_key=True
    )
    assid: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True
    )
    timeadded: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    timemodified: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    submissiontext: Mapped[str] = mapped_column(Text, nullable=False)
    grade: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    gradedby: Mapped[str | None] = mapped_column(
        ForeignKey("users.email", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["courseid", "assid"],
            ["course_assignments.courseid", "course_assignments.assid"],
            ondelete="CASCADE",
        ),
        CheckConstraint("timemodified >= timeadded"),
        CheckConstraint("length(submissiontext) BETWEEN 3 AND 10000"),
        CheckConstraint("comment IS NULL OR length(comment) BETWEEN 3 AND 10000"),
    )
