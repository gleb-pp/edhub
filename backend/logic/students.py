from repo.users import User
from repo.courses import Course
from repo.students import StudentAt
from sqlalchemy.orm import Session
from sqlalchemy import exists
import exceptions.students as student_errors


def check_student_access(user: User, course: Course, db: Session) -> bool:
    """Check whether the provided user has a student role in the provided course."""
    return db.query(
        exists().where(
            (StudentAt.email == user.email) &
            (StudentAt.course_id == course.course_id)
        )
    ).scalar()


def assert_student_access(user: User, course: Course, db: Session) -> bool:
    """Asserts that the provided user has a student role in the provided course."""
    if not check_student_access(user, course, db):
        raise student_errors.StudentRoleRequired(user.email, course.title)


def assert_not_student(user: User, course: Course, db: Session) -> None:
    """Asserts that the provided user is already student in the provided course."""
    if check_student_access(user, course, db):
        raise student_errors.StudentRoleConflict(user.email, course.course_id)


def get_enrolled_students(course: Course, db: Session) -> list[User]:
    """Get the list of students enrolled to the provided course."""
    return (
        db.query(User)
        .join(StudentAt, StudentAt.email == User.email)
        .filter(StudentAt.course_id == course.course_id)
        .order_by(User.name, User.email)
        .all()
    )


def invite_student(student: User, course: Course, db: Session) -> None:
    """Invite the provided student to the provided course."""
    student_at = StudentAt(email=student.email, course_id=course.course_id)
    db.add(student_at)


def remove_student(student: User, course: Course, db: Session) -> None:
    """Remove the provided student from the provided course."""
    db.delete(
        db.query(StudentAt).filter(
            StudentAt.email == student.email,
            StudentAt.course_id == course.course_id
        ).first()
    )
