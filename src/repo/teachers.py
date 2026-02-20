from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.repo.base import Base


class Teaches(Base):
    """SQLAlchemy model for the association between teachers and courses."""

    __tablename__ = "teaches"

    email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True,
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True,
    )
