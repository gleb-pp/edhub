from repo.users import User
from repo.courses import Course
from repo.teachers import Teaches
from sqlalchemy.orm import Session
from sqlalchemy import exists
import exceptions.teachers as teacher_errors
import logging


class TeacherService:
    """Service class for teacher-related operations."""

    logger = logging.getLogger("TeacherService")

    def __init__(self, db: Session):
        self.db = db

    def check_instructor_access(self, user: User, course: Course) -> bool:
        """Check whether the provided user has an instructor role in the provided course."""
        return self.db.query(
            exists().where(
                (Course.instructor == user.email)
                & (Course.course_id == course.course_id)
            )
        ).scalar()

    def check_teacher_access(self, user: User, course: Course) -> bool:
        """Check whether the provided user has a teacher or instructor role in the provided course."""
        if course.instructor == user.email:
            return True

        return self.db.query(
            exists().where(
                (Teaches.email == user.email) & (Teaches.course_id == course.course_id)
            )
        ).scalar()

    def assert_instructor_access(self, user: User, course: Course) -> None:
        """Asserts that the provided user has an instructor role in the provided course."""
        if not self.check_instructor_access(user, course):
            self.logger.warning(
                f"Attempt to access instructor-only actions by user {user.email} on course {course.name}"
            )
            raise teacher_errors.InstructorRoleRequired(user.email, course.name)

    def assert_teacher_access(self, user: User, course: Course) -> None:
        """Asserts that the provided user has a teacher or an instructor role in the provided course."""
        if not self.check_teacher_access(user, course):
            self.logger.warning(
                f"Attempt to access teacher-only actions by user {user.email} on course {course.name}"
            )
            raise teacher_errors.TeacherRoleRequired(user.email, course.name)

    def assert_not_teacher(self, user: User, course: Course) -> None:
        """Asserts that the provided user is already a teacher in the provided course."""
        if self.check_teacher_access(user, course):
            self.logger.warning(
                f"Attempt to assign teacher role to user {user.email} who is already a teacher in course {course.name}"
            )
            raise teacher_errors.TeacherRoleConflict(user.email, course.course_id)

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
