from repo.users import User
from repo.courses import Course
from repo.teachers import Teaches
from sqlalchemy.orm import Session
import logging


class TeacherService:
    """Service class for teacher-related operations."""

    logger = logging.getLogger("TeacherService")

    def __init__(self, db: Session):
        self.db = db

    def get_course_teachers(self, course: Course) -> list[User]:
        """Get the list of students enrolled to the provided course."""
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
        self.logger.info(f"Invited teacher {teacher.email} to course {course.name}")

    def remove_teacher(self, teacher: User, course: Course) -> None:
        """Remove the provided teacher from the provided course."""
        self.db.delete(
            self.db.query(Teaches)
            .filter(
                Teaches.email == teacher.email, Teaches.course_id == course.course_id
            )
            .first()
        )
        self.db.flush()
        self.logger.info(f"Removed teacher {teacher.email} from course {course.name}")

    def change_course_instructor(
        self, instructor: User, teacher: User, course: Course
    ) -> None:
        """Change the instructor to some teacher within the provided course."""
        course.instructor = teacher.email
        self.remove_teacher(teacher, course)
        self.invite_teacher(instructor, course)
        self.db.flush()
        self.logger.info(
            f"Changed instructor of course {course.name} to {teacher.email}"
        )
