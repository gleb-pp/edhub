import logging

from sqlalchemy.orm import Session

from src.repo.courses import Course
from src.repo.teachers import Teaches
from src.repo.users import User


class TeacherService:
    """Service class for teacher-related operations."""

    logger = logging.getLogger(__name__)

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_course_teachers(self, course: Course) -> list[User]:
        """Get the list of teachers enrolled to the provided course."""
        return (
            self.db.query(User)
            .join(Teaches, Teaches.email == User.email)
            .filter(Teaches.course_id == course.course_id)
            .order_by(User.name, User.email)
            .all()
        )

    def invite_teacher(self, teacher: User, course: Course) -> None:
        """Invite the provided teacher to the provided course."""
        teaches = Teaches(email=teacher.email, course_id=course.course_id)
        self.db.add(teaches)
        self.logger.info(f"Invited teacher {teacher.email} to course {course.course_id}")

    def remove_teacher(self, teacher: User, course: Course) -> None:
        """Remove the provided teacher from the provided course."""
        teaches = (
            self.db.query(Teaches)
            .filter(
                Teaches.email == teacher.email, 
                Teaches.course_id == course.course_id,
            )
            .first()
        )
        if teaches:
            self.db.delete(teaches)
            self.logger.info(f"Removed teacher {teacher.email} from course {course.course_id}")

    def change_course_instructor(
        self, instructor: User, teacher: User, course: Course,
    ) -> None:
        """Change the instructor to some teacher within the provided course."""
        old_instructor_email = course.instructor
        course.instructor = teacher.email
        self.remove_teacher(teacher, course)
        if old_instructor_email != teacher.email:
            self.invite_teacher(instructor, course)
        self.db.flush()
        self.logger.info(
            f"Changed instructor of course {course.course_id} from {old_instructor_email} to {teacher.email}",
        )
