from repo.users import User
from repo.courses import Course
from repo.students import StudentAt
from sqlalchemy.orm import Session
from sqlalchemy import exists
import exceptions.students as student_errors
import services.parents as parent_logic
import services.teachers as teacher_logic
import services.courses as course_logic
import logging


class StudentService:
    """Service class for managing student-related operations."""

    logger = logging.getLogger("StudentService")

    def __init__(self, db: Session):
        self.db = db

    def check_student_access(self, user: User, course: Course) -> bool:
        """Check whether the provided user has a student role in the provided course."""
        return self.db.query(
            exists().where(
                (StudentAt.email == user.email)
                & (StudentAt.course_id == course.course_id)
            )
        ).scalar()

    def assert_student_access(self, user: User, course: Course) -> None:
        """Asserts that the provided user has a student role in the provided course."""
        if not self.check_student_access(user, course):
            self.logger.warning(
                f"User {user.email} does not have student access in course {course.course_id}"
            )
            raise student_errors.StudentRoleRequired(user.email, course.title)

    def assert_not_student(self, user: User, course: Course) -> None:
        """Asserts that the provided user is already student in the provided course."""
        if self.check_student_access(user, course):
            self.logger.warning(
                f"Attempt to add student role to user {user.email} who is already a student in course {course.course_id}"
            )
            raise student_errors.StudentRoleConflict(user.email, course.course_id)

    def get_enrolled_students(self, course: Course) -> list[User]:
        """Get the list of students enrolled to the provided course.

        Students are ordered by name, then by email."""
        return (
            self.db.query(User)
            .join(StudentAt, StudentAt.email == User.email)
            .filter(StudentAt.course_id == course.course_id)
            .order_by(User.name, User.email)
            .all()
        )

    def invite_student(self, student: User, course: Course) -> None:
        """Invite the provided student to the provided course."""
        self.logger.info(
            f"Inviting student {student.email} to course {course.course_id}"
        )
        student_at = StudentAt(email=student.email, course_id=course.course_id)
        self.db.add(student_at)
        self.db.flush()

    def remove_student(self, student: User, course: Course) -> None:
        """Remove the provided student from the provided course."""
        self.logger.info(
            f"Removing student {student.email} from course {course.course_id}"
        )
        self.db.delete(
            self.db.query(StudentAt)
            .filter(
                StudentAt.email == student.email,
                StudentAt.course_id == course.course_id,
            )
            .first()
        )
        self.db.flush()

    def assert_access_to_student(
        self, student: User, user: User, course: Course
    ) -> None:
        """Asserts that the provided user has access to the provided student."""
        course_logic.assert_course_access(user, course, self.db)
        self.assert_student_access(student, course)
        if not (
            teacher_logic.check_teacher_access(user, course, self.db)
            or user.email == student.email
            or parent_logic.check_parent_of_student(user, student, course, self.db)
            or user.isadmin
        ):
            self.logger.warning(
                f"User {user.email} does not have access to student {student.email} info in course {course.course_id}"
            )
            raise student_errors.NoAccessToStudentInfo(
                student.email, user.email, course.id
            )
