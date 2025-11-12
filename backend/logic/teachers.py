from repo.users import User
from repo.courses import Course
from repo.teachers import Teaches
from sqlalchemy.orm import Session
from sqlalchemy import exists

def check_instructor_access(user: User, course: Course, db: Session) -> bool:
    """Check whether the provided user has an instructor role in the provided course."""
    return db.query(
        exists().where(
            (Course.instructor == user.email) &
            (Course.course_id == course.courseid)
        )
    ).scalar()


def check_teacher_access(user: User, course: Course, db: Session) -> bool:
    """Check whether the provided user has a teacher role in the provided course."""
    return db.query(
        exists().where(
            (Teaches.email == user.email) &
            (Teaches.courseid == course.courseid)
        )
    ).scalar()
