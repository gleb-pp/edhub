import logging

from sqlalchemy.orm import Session

from src.repo.courses import Course
from src.repo.parents import ParentAt
from src.repo.users import User


class ParentService:
    """Service for managing parent roles in courses."""

    logger = logging.getLogger(__name__)

    def __init__(self, db: Session):
        self.db = db

    def invite_parent(self, parent: User, student: User, course: Course) -> None:
        """Invite the provided parent to the provided course."""
        self.logger.info(
            f"Inviting parent {parent.email} to course {course.course_id} for student {student.email}"
        )
        parent_of = ParentAt(
            parent_email=parent.email,
            student_email=student.email,
            course_id=course.course_id,
        )
        self.db.add(parent_of)

    def remove_parent_student(
        self, parent: User, student: User, course: Course
    ) -> None:
        """Remove the provided parent from observing the provided student within the provided course."""
        self.logger.info(
            f"Removing parent {parent.email} from student {student.email} in course {course.course_id}"
        )
        self.db.delete(
            self.db.query(ParentAt)
            .filter(
                ParentAt.parent_email == parent.email,
                ParentAt.student_email == student.email,
                ParentAt.course_id == course.course_id,
            )
            .first()
        )
        self.db.flush()

    def remove_parent(self, parent: User, course: Course) -> None:
        """Remove the provided parent from the provided course."""
        self.logger.info(
            f"Removing parent {parent.email} from course {course.course_id}"
        )
        self.db.delete(
            self.db.query(ParentAt)
            .filter(
                ParentAt.parent_email == parent.email,
                ParentAt.course_id == course.course_id,
            )
            .first()
        )

    def get_students_parents(self, student: User, course: Course) -> list[User]:
        """Get the list of parents observing the provided student within the provided course."""
        return (
            self.db.query(User)
            .join(ParentAt, ParentAt.parent_email == User.email)
            .filter(
                ParentAt.student_email == student.email,
                ParentAt.course_id == course.course_id,
            )
            .all()
        )

    def get_parents_children(self, parent: User, course: Course) -> list[User]:
        """Get the list of students that the provided parent observes within the provided course."""
        return (
            self.db.query(User)
            .join(ParentAt, ParentAt.student_email == User.email)
            .filter(
                ParentAt.parent_email == parent.email,
                ParentAt.course_id == course.course_id,
            )
            .all()
        )
