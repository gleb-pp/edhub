import logging

from sqlalchemy.orm import Session

from src.exceptions import courses as course_errors
from src.repo.courses import Course
from src.repo.personalization import PersonalCourseInfo
from src.repo.users import User


class CourseService:
    """Service class for managing courses."""

    logger = logging.getLogger(__name__)

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_course(self, course_id: str) -> Course:
        """Check whether a user with provided email exists in the system."""
        course = self.db.query(Course).filter(Course.course_id == course_id).first()
        if not course:
            self.logger.warning(f"Attempt to access non-existing course {course_id}")
            raise course_errors.CourseNotFoundError(course_id)
        return course

    def get_available_courses(self, user: User) -> list[Course]:
        """Get the list of courses available to user."""
        return (
            self.db.query(Course)
            .join(PersonalCourseInfo, PersonalCourseInfo.course_id == Course.course_id)
            .filter(PersonalCourseInfo.email == user.email)
            .order_by(PersonalCourseInfo.course_order.asc())
            .all()
        )

    def get_all_courses(self) -> list[Course]:
        """Get the list of all courses within the platform."""
        return self.db.query(Course).all()

    def create_course(self, title: str, organization: str | None, user: User) -> Course:
        """Create the course with the provided parameters."""
        self.logger.info(
            f"Creating course '{title}' for organization '{organization}' by user {user.email}.",
        )
        course = Course(title=title, organization=organization, instructor=user.email)
        self.db.add(course)
        self.db.flush()
        return course

    def delete_course(self, course: Course) -> None:
        """Delete the provided course from the system."""
        self.logger.info(f"Deleting course {course.course_id}.")
        self.db.delete(course)
