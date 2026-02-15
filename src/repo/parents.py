from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.repo.base import Base


class ParentAt(Base):
    __tablename__ = "parent_at"

    parent_email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True,
    )
    student_email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True,
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True,
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["student_email", "course_id"],
            ["student_at.email", "student_at.course_id"],
            ondelete="CASCADE",
        ),
    )
