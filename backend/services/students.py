from repo.users import User
from repo.courses import Course
from repo.students import StudentAt
from sqlalchemy.orm import Session
import logging


class StudentService:
    """Service class for managing student-related operations."""

    logger = logging.getLogger("StudentService")

    def __init__(self, db: Session):
        self.db = db

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
