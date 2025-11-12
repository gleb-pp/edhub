from sqlalchemy import Integer, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from repo.base import Base


class PersonalCourseInfo(Base):
    __tablename__ = "personal_course_info"

    courseid: Mapped[str] = mapped_column(
        ForeignKey("courses.courseid", ondelete="CASCADE"), primary_key=True
    )
    email: Mapped[str] = mapped_column(
        ForeignKey("users.email", ondelete="CASCADE"), primary_key=True
    )
    emojiid: Mapped[int | None] = mapped_column(Integer)
    courseorder: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("email", "courseorder", name="personal_course_info_email_courseorder_key"),
        CheckConstraint("emojiid IS NULL OR (emojiid BETWEEN 0 AND 80)"),
        CheckConstraint("courseorder >= 0"),
    )
