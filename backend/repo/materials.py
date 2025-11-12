from sqlalchemy import Integer, DateTime, Text, CheckConstraint, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from repo.base import Base


class CourseMaterial(Base):
    __tablename__ = "course_materials"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True
    )
    matid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timeadded: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    author: Mapped[str | None] = mapped_column(
        ForeignKey("users.email", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    section_id: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["course_id", "section_id"],
            ["course_sections.course_id", "course_sections.section_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("length(name) BETWEEN 3 AND 80"),
        CheckConstraint("length(description) BETWEEN 3 AND 10000"),
    )
