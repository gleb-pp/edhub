from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from repo.base import Base


class ParentAt(Base):
    __tablename__ = "parent_at"

    parentemail: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True
    )
    studentemail: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True
    )
    courseid: Mapped[str] = mapped_column(
        ForeignKey("courses.courseid", ondelete="CASCADE"), primary_key=True
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["studentemail", "courseid"],
            ["student_at.email", "email.courseid"],
            ondelete="CASCADE",
        ),
    )
