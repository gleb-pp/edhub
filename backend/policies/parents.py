from repo.users import User
from repo.courses import Course
from repo.parents import ParentAt
from sqlalchemy.orm import Session
from sqlalchemy import exists
import exceptions.parents as parent_errors
from .courses import CoursePolicy
from .teachers import TeacherPolicy


class ParentPolicy:
    """Policy class for handling parent-related assertions."""

    @staticmethod
    def check_parent_access(user: User, course: Course, db: Session) -> bool:
        """Check whether the provided user has a parent role in the provided course."""
        return db.query(
            exists().where(
                (ParentAt.parent_email == user.email)
                & (ParentAt.course_id == course.course_id)
            )
        ).scalar()

    @staticmethod
    def assert_parent_access(parent: User, course: Course, db: Session) -> None:
        """Asserts that the provided user has a parent role in the provided course."""
        if not ParentPolicy.check_parent_access(parent, course, db):
            raise parent_errors.ParentRoleRequired(parent.email, course.course_id)

    @staticmethod
    def assert_not_parent(user: User, course: Course, db: Session) -> None:
        """Asserts that the provided user is already a parent in the provided course."""
        if ParentPolicy.check_parent_access(user, course, db):
            raise parent_errors.ParentRoleConflict(user.email, course.course_id)

    @staticmethod
    def check_parent_of_student(
        parent: User, student: User, course: Course, db: Session
    ) -> bool:
        """Check whether the provided user is a parent of the student in the provided course."""
        return db.query(
            exists().where(
                (ParentAt.parent_email == parent.email)
                & (ParentAt.student_email == student.email)
                & (ParentAt.course_id == course.course_id)
            )
        ).scalar()

    @staticmethod
    def assert_not_parent_of_student(
        parent: User, student: User, course: Course, db: Session
    ) -> None:
        """Asserts that the provided user is not a parent of the student in the provided course."""
        if ParentPolicy.check_parent_of_student(parent, student, course, db):
            raise parent_errors.ParentOfStudentRoleConflict(
                parent.email, student.email, course.course_id
            )

    @staticmethod
    def assert_parent_of_student(
        parent: User, student: User, course: Course, db: Session
    ) -> None:
        """Asserts that the provided user is already parent of the student in the provided course."""
        if not ParentPolicy.check_parent_of_student(parent, student, course, db):
            raise parent_errors.ParentOfStudentRoleRequired(
                parent.email, student.email, course.course_id
            )

    @staticmethod
    def assert_access_to_parent(
        parent: User, user: User, course: Course, db: Session
    ) -> None:
        """Asserts that the provided user has access to the provided parent."""
        CoursePolicy.assert_course_access(user, course, db)
        ParentPolicy.assert_parent_access(parent, course, db)
        if not (
            TeacherPolicy.check_teacher_access(user, course, db)
            or user.email == parent.email
            or user.isadmin
        ):
            raise parent_errors.NoAccessToParentInfo(
                parent.email, user.email, course.course_id
            )
