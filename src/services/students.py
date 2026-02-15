import logging

from sqlalchemy.orm import Session

from src.repo.courses import Course
from src.repo.students import StudentAt
from src.repo.users import User


class StudentService:
    """Service class for managing student-related operations."""

    logger = logging.getLogger(__name__)

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_enrolled_students(self, course: Course) -> list[User]:
        """
        Get the list of students enrolled to the provided course.

        Students are ordered by name, then by email.
        """
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
            f"Inviting student {student.email} to course {course.course_id}",
        )
        student_at = StudentAt(email=student.email, course_id=course.course_id)
        self.db.add(student_at)
        self.db.flush()

    def remove_student(self, student: User, course: Course) -> None:
        """Remove the provided student from the provided course."""
        self.logger.info(
            f"Removing student {student.email} from course {course.course_id}",
        )
        student_at = (
            self.db.query(StudentAt)
            .filter(
                StudentAt.email == student.email,
                StudentAt.course_id == course.course_id,
            )
            .first()
        )
        if student_at:
            self.db.delete(student_at)
            self.db.flush()
