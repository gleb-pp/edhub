from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from repo.base import Base


class StudentAt(Base):
    __tablename__ = "student_at"

    email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True
    )
    courseid: Mapped[str] = mapped_column(
        ForeignKey("courses.courseid", ondelete="CASCADE"), primary_key=True
    )
