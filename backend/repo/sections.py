from sqlalchemy import Integer, Text, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from repo.base import Base


class CourseSection(Base):
    """Database model for the course sections."""

    __tablename__ = "course_section"
    
    courseid: Mapped[str] = mapped_column(
        ForeignKey("courses.courseid", ondelete="CASCADE"), primary_key=True
    )
    sectionid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sectionorder: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("courseid", "sectionorder", name="course_sections_courseid_sectionorder_key"),
        CheckConstraint("length(name) BETWEEN 3 AND 80"),
        CheckConstraint("sectionorder >= 0"),
    )
