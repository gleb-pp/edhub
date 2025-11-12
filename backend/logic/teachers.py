from repo.users import User
from repo.courses import Course
from repo.teachers import Teaches
from sqlalchemy.orm import Session
from sqlalchemy import exists
import exceptions.teachers as teacher_errors

def check_instructor_access(user: User, course: Course, db: Session) -> bool:
    """Check whether the provided user has an instructor role in the provided course."""
    return db.query(
        exists().where(
            (Course.instructor == user.email) &
            (Course.course_id == course.course_id)
        )
    ).scalar()


def check_teacher_access(user: User, course: Course, db: Session) -> bool:
    """Check whether the provided user has a teacher role in the provided course."""
    return db.query(
        exists().where(
            (Teaches.email == user.email) &
            (Teaches.course_id == course.course_id)
        )
    ).scalar()


def assert_instructor_access(user: User, course: Course, db: Session) -> None:
    """Asserts that the provided user has an instructor role in the provided course."""
    if not check_instructor_access(user, course, db):
        raise teacher_errors.InstructorRoleRequired(user.email, course.name)
