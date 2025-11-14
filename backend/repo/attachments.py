from sqlalchemy import Integer, DateTime, Text, CheckConstraint, Uuid, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from repo.base import Base


class MaterialFile(Base):
    __tablename__ = "material_files"

    course_id: Mapped[str] = mapped_column(Uuid, primary_key=True)
    material_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fileid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploadtime: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("length(filename) <= 80"),
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
    uploadtime: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("length(filename) <= 80"),
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
    uploadtime: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("length(filename) <= 80"),
        ForeignKeyConstraint(
            ["course_id", "assignment_id", "email"],
            ["course_assignments_submissions.course_id", "course_assignments_submissions.assignment_id", "course_assignments_submissions.email"],
            ondelete="CASCADE",
        ),
    )
