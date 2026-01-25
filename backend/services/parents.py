from repo.users import User
from repo.courses import Course
from repo.parents import ParentAt
from sqlalchemy.orm import Session
from sqlalchemy import exists
import exceptions.parents as parent_errors
import services.courses as course_logic
import services.teachers as teacher_logic
import logging


class ParentService:
    """Service for managing parent roles in courses."""

    logger = logging.getLogger("ParentService")

    def __init__(self, db: Session):
        self.db = db

    def check_parent_access(self, user: User, course: Course) -> bool:
        """Check whether the provided user has a parent role in the provided course."""
        return self.db.query(
            exists().where(
                (ParentAt.parent_email == user.email)
                & (ParentAt.course_id == course.course_id)
            )
        ).scalar()

    def assert_parent_access(self, parent: User, course: Course) -> None:
        """Asserts that the provided user has a parent role in the provided course."""
        if not self.check_parent_access(parent, course):
            self.logger.warning(
                f"User {parent.email} does not have parent access in course {course.course_id}"
            )
            raise parent_errors.ParentRoleRequired(parent.email, course.course_id)

    def assert_not_parent(self, user: User, course: Course) -> None:
        """Asserts that the provided user is already a parent in the provided course."""
        if self.check_parent_access(user, course):
            self.logger.warning(
                f"Attempt to add parent role to user {user.email} who is already a parent in course {course.course_id}"
            )
            raise parent_errors.ParentRoleConflict(user.email, course.course_id)

    def check_parent_of_student(
        self, parent: User, student: User, course: Course
    ) -> bool:
        """Check whether the provided user is a parent of the student in the provided course."""
        return self.db.query(
            exists().where(
                (ParentAt.parent_email == parent.email)
                & (ParentAt.student_email == student.email)
                & (ParentAt.course_id == course.course_id)
            )
        ).scalar()

    def assert_not_parent_of_student(
        self, parent: User, student: User, course: Course
    ) -> None:
        """Asserts that the provided user is not a parent of the student in the provided course."""
        if self.check_parent_of_student(parent, student, course):
            self.logger.warning(
                f"User {parent.email} is already a parent of student {student.email} in course {course.course_id}"
            )
            raise parent_errors.ParentOfStudentRoleConflict(
                parent.email, student.email, course.course_id
            )

    def assert_parent_of_student(
        self, parent: User, student: User, course: Course
    ) -> None:
        """Asserts that the provided user is already parent of the student in the provided course."""
        if not self.check_parent_of_student(parent, student, course):
            self.logger.warning(
                f"User {parent.email} is not a parent of student {student.email} in course {course.course_id}"
            )
            raise parent_errors.ParentOfStudentRoleRequired(
                parent.email, student.email, course.course_id
            )

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

    def assert_access_to_parent(self, parent: User, user: User, course: Course) -> None:
        """Asserts that the provided user has access to the provided parent."""
        course_logic.assert_course_access(user, course, self.db)
        self.assert_parent_access(parent, course)
        if not (
            teacher_logic.check_teacher_access(user, course, self.db)
            or user.email == parent.email
            or user.isadmin
        ):
            self.logger.warning(
                f"User {user.email} does not have access to parent {parent.email} in course {course.course_id}"
            )
            raise parent_errors.NoAccessToParentInfo(
                parent.email, user.email, course.id
            )
