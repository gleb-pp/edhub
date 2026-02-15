from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.repo.base import Base
from src.settings.course import course_settings


class MaterialFile(Base):
    __tablename__ = "material_files"

    course_id: Mapped[str] = mapped_column(Uuid, primary_key=True)
    material_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fileid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploadtime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=UTC)
    )

    __table_args__ = (
        CheckConstraint(f"length(filename) <= {course_settings.filename_max_lenght}"),
        ForeignKeyConstraint(
            ["course_id", "material_id"],
            ["course_materials.course_id", "course_materials.material_id"],
            ondelete="CASCADE",
        ),
    )


class AssignmentFile(Base):
    __tablename__ = "assignment_files"

    course_id: Mapped[str] = mapped_column(Uuid, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fileid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploadtime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=UTC)
    )

    __table_args__ = (
        CheckConstraint(f"length(filename) <= {course_settings.filename_max_lenght}"),
        ForeignKeyConstraint(
            ["course_id", "assignment_id"],
            ["course_assignments.course_id", "course_assignments.assignment_id"],
            ondelete="CASCADE",
        ),
    )


class SubmissionFile(Base):
    __tablename__ = "submission_files"

    course_id: Mapped[str] = mapped_column(Uuid, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(Text, primary_key=True)
    fileid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploadtime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(tz=UTC)
    )

    __table_args__ = (
        CheckConstraint(f"length(filename) <= {course_settings.filename_max_lenght}"),
        ForeignKeyConstraint(
            ["course_id", "assignment_id", "email"],
            [
                "course_assignments_submissions.course_id",
                "course_assignments_submissions.assignment_id",
                "course_assignments_submissions.email",
            ],
            ondelete="CASCADE",
        ),
    )
