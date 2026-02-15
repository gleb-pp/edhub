from sqlalchemy import exists
from sqlalchemy.orm import Session

import src.exceptions.students as student_errors
from src.repo.courses import Course
from src.repo.students import StudentAt
from src.repo.users import User

from .courses import CoursePolicy
from .parents import ParentPolicy
from .teachers import TeacherPolicy


class StudentPolicy:
    """Policy class for handling student-related assertions."""

    @staticmethod
    def check_student_access(user: User, course: Course, db: Session) -> bool:
        """Check whether the provided user has a student role in the provided course."""
        return db.query(
            exists().where(
                (StudentAt.email == user.email)
                & (StudentAt.course_id == course.course_id)
            )
        ).scalar()

    @staticmethod
    def assert_student_access(user: User, course: Course, db: Session) -> None:
        """Asserts that the provided user has a student role in the provided course."""
        if not StudentPolicy.check_student_access(user, course, db):
            raise student_errors.StudentRoleRequiredError(user.email, course.title)

    @staticmethod
    def assert_not_student(user: User, course: Course, db: Session) -> None:
        """Asserts that the provided user is already student in the provided course."""
        if StudentPolicy.check_student_access(user, course, db):
            raise student_errors.StudentRoleConflictError(user.email, course.course_id)

    @staticmethod
    def assert_access_to_student(
        student: User, user: User, course: Course, db: Session
    ) -> None:
        """Asserts that the provided user has access to the provided student."""
        CoursePolicy.assert_course_access(user, course, db)
        StudentPolicy.assert_student_access(student, course, db)
        if not (
            TeacherPolicy.check_teacher_access(user, course, db)
            or user.email == student.email
            or ParentPolicy.check_parent_of_student(user, student, course, db)
            or user.isadmin
        ):
            raise student_errors.NoAccessToStudentInfoError(
                student.email, user.email, course.id
            )
