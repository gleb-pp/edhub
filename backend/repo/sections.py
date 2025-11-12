from sqlalchemy import Integer, Text, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from repo.base import Base


class CourseSection(Base):
    """Database model for the course sections."""

    __tablename__ = "course_sections"
    
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True
    )
    section_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("course_id", "section_order", name="course_sections_course_id_section_order_key"),
        CheckConstraint("length(name) BETWEEN 3 AND 80"),
        CheckConstraint("section_order >= 0"),
    )
