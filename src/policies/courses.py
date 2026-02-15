from sqlalchemy import exists
from sqlalchemy.orm import Session

from src.exceptions import courses as course_errors
from src.repo.courses import Course
from src.repo.personalization import PersonalCourseInfo
from src.repo.users import User


class CoursePolicy:
    """Policy class for course-related actions."""

    @staticmethod
    def assert_course_access(user: User, course: Course, db: Session) -> None:
        """Asserts that the provided user has an access to the provided course."""
        access = db.query(
            exists().where(
                (PersonalCourseInfo.email == user.email)
                & (PersonalCourseInfo.course_id == course.course_id)
            )
        ).scalar()
        if not access:
            raise course_errors.ParticipantRoleRequiredError(user.email, course.course_id)
