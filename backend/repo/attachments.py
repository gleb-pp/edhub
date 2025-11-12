from sqlalchemy import Integer, DateTime, Text, CheckConstraint, Uuid, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from repo.base import Base


class MaterialFile(Base):
    __tablename__ = "material_files"

    courseid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    matid: Mapped[int] = mapped_column(Integer, primary_key=True)
    fileid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploadtime: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("length(filename) <= 80"),
        ForeignKeyConstraint(
            ["courseid", "matid"],
            ["course_materials.courseid", "course_materials.matid"],
            ondelete="CASCADE",
        ),
    )


class AssignmentFile(Base):
    __tablename__ = "assignment_files"

    courseid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    assid: Mapped[int] = mapped_column(Integer, primary_key=True)
    fileid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploadtime: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("length(filename) <= 80"),
        ForeignKeyConstraint(
            ["courseid", "matid"],
            ["course_assignments.courseid", "course_assignments.assid"],
            ondelete="CASCADE",
        ),
    )


class SubmissionFile(Base):
    __tablename__ = "submission_files"

    courseid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    assid: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(Text, primary_key=True)
    fileid: Mapped[str] = mapped_column(Uuid, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploadtime: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("length(filename) <= 80"),
        ForeignKeyConstraint(
            ["courseid", "assid", "email"],
            ["course_assignments_submissions.courseid", "course_assignments_submissions.assid", "course_assignments_submissions.email"],
            ondelete="CASCADE",
        ),
    )
