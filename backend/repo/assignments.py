from sqlalchemy import Integer, DateTime, Text, CheckConstraint, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from repo.base import Base


class CourseAssignment(Base):
    __tablename__ = "course_assignments"

    courseid: Mapped[str] = mapped_column(
        ForeignKey("courses.courseid", ondelete="CASCADE"), primary_key=True
    )
    assid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timeadded: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    author: Mapped[str | None] = mapped_column(
        ForeignKey("users.email", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sectionid: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["courseid", "sectionid"],
            ["course_sections.courseid", "course_sections.sectionid"],
            ondelete="CASCADE",
        ),
        CheckConstraint("length(name) BETWEEN 3 AND 80"),
        CheckConstraint("length(description) BETWEEN 3 AND 10000"),
    )
