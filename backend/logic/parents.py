from repo.users import User
from repo.courses import Course
from repo.parents import ParentAt
from sqlalchemy.orm import Session
from sqlalchemy import exists
import exceptions.parents as parent_errors


def check_parent_access(user: User, course: Course, db: Session) -> bool:
    """Check whether the provided user has a parent role in the provided course."""
    return db.query(
        exists().where(
            (ParentAt.parent_email == user.email) &
            (ParentAt.course_id == course.course_id)
        )
    ).scalar()


def assert_not_parent(user: User, course: Course, db: Session) -> None:
    """Asserts that the provided user is already a parent in the provided course."""
    if check_parent_access(user, course, db):
        raise parent_errors.ParentRoleConflict(user.email, course.course_id)

