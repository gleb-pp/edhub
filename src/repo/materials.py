from sqlalchemy import (
    Integer,
    DateTime,
    Text,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from src.settings.materials import material_settings
from src.repo.base import Base


class CourseMaterial(Base):
    __tablename__ = "course_materials"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True
    )
    material_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    section_id: Mapped[int] = mapped_column(Integer, nullable=False)
    creation_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=timezone.utc)
    )
    author: Mapped[str | None] = mapped_column(
        ForeignKey("users.email", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["course_id", "section_id"],
            ["course_sections.course_id", "course_sections.section_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            f"length(title) BETWEEN {material_settings.name_min_lenght} AND {material_settings.name_max_lenght}"
        ),
        CheckConstraint(
            f"length(description) BETWEEN {material_settings.description_min_lenght} AND {material_settings.description_max_lenght}"
        ),
    )
