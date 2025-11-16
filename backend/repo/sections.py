from sqlalchemy import Integer, Text, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from settings.sections import section_settings

from repo.base import Base


class CourseSection(Base):
    """Database model for the course sections."""

    __tablename__ = "course_sections"
    
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True
    )
    section_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "section_order",
            name="course_sections_course_id_section_order_key",
            deferrable=True,
            initially="DEFERRED"
        ),
        CheckConstraint(f"length(title) BETWEEN {section_settings.name_min_lenght} AND {section_settings.name_max_lenght}"),
        CheckConstraint("section_order >= 0"),
    )
