from sqlalchemy import exists
from sqlalchemy.orm import Session

import src.exceptions.teachers as teacher_errors
from src.repo.courses import Course
from src.repo.teachers import Teaches
from src.repo.users import User


class TeacherPolicy:
    """Policy class for handling teacher-related assertions."""

    @staticmethod
    def check_instructor_access(user: User, course: Course, db: Session) -> bool:
        """Check whether the provided user has an instructor role in the provided course."""
        return db.query(
            exists().where(
                (Course.instructor == user.email)
                & (Course.course_id == course.course_id)
            )
        ).scalar()

    @staticmethod
    def check_teacher_access(user: User, course: Course, db: Session) -> bool:
        """Check whether the provided user has a teacher or instructor role in the provided course."""
        if course.instructor == user.email:
            return True

        return db.query(
            exists().where(
                (Teaches.email == user.email) & (Teaches.course_id == course.course_id)
            )
        ).scalar()

    @staticmethod
    def assert_instructor_access(user: User, course: Course, db: Session) -> None:
        """Asserts that the provided user has an instructor role in the provided course."""
        if not TeacherPolicy.check_instructor_access(user, course, db):
            raise teacher_errors.InstructorRoleRequiredError(user.email, course.name)

    @staticmethod
    def assert_teacher_access(user: User, course: Course, db: Session) -> None:
        """Asserts that the provided user has a teacher or an instructor role in the provided course."""
        if not TeacherPolicy.check_teacher_access(user, course, db):
            raise teacher_errors.TeacherRoleRequiredError(user.email, course.name)

    @staticmethod
    def assert_not_teacher(user: User, course: Course, db: Session) -> None:
        """Asserts that the provided user is already a teacher in the provided course."""
        if TeacherPolicy.check_teacher_access(user, course, db):
            raise teacher_errors.TeacherRoleConflictError(user.email, course.course_id)
