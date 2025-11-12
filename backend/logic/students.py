from repo.users import User
from repo.courses import Course
from repo.students import StudentAt
from sqlalchemy.orm import Session
from sqlalchemy import exists


def check_student_access(user: User, course: Course, db: Session) -> bool:
    """Check whether the provided user has a student role in the provided course."""
    return db.query(
        exists().where(
            (StudentAt.email == user.email) &
            (StudentAt.courseid == course.courseid)
        )
    ).scalar()
