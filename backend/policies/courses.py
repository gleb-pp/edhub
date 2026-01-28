from sqlalchemy import exists
from exceptions import courses as course_errors
from sqlalchemy.orm import Session
from repo.courses import Course
from repo.users import User
from repo.personalization import PersonalCourseInfo


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
            raise course_errors.ParticipantRoleRequired(user.email, course.course_id)
