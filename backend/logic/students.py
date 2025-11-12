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
            (StudentAt.course_id == course.course_id)
        )
    ).scalar()


def get_enrolled_students(course: Course, db: Session) -> list[User]:
    """Get the list of students enrolled to the provided course."""
    return (
        db.query(User)
        .join(StudentAt, StudentAt.email == User.email)
        .filter(StudentAt.course_id == course.course_id)
        .order_by(User.name, User.email)
        .all()
    )
