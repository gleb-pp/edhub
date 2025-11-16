from sqlalchemy import Integer, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from repo.base import Base
from settings.course import course_settings


class PersonalCourseInfo(Base):
    __tablename__ = "personal_course_info"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), primary_key=True
    )
    email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True
    )
    emoji_id: Mapped[int | None] = mapped_column(Integer)
    course_order: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "email", 
            "course_order", 
            name="personal_course_info_email_course_order_key",
            deferrable=True,
            initially="DEFERRED"
        ),
        CheckConstraint(f"emojiid IS NULL OR (emojiid BETWEEN 0 AND {course_settings.emoji_count - 1})"),
        CheckConstraint("course_order >= 0"),
    )
