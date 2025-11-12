from repo.users import User
from repo.courses import Course
from repo.parents import ParentAt
from sqlalchemy.orm import Session
from sqlalchemy import exists


def check_parent_access(user: User, course: Course, db: Session) -> bool:
    """Check whether the provided user has a parent role in the provided course."""
    return db.query(
        exists().where(
            (ParentAt.parentemail == user.email) &
            (ParentAt.courseid == course.course_id)
        )
    ).scalar()
