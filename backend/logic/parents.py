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


def assert_parent_access(parent: User, course: Course, db: Session) -> None:
    """Asserts that the provided user has a parent role in the provided course."""
    if not check_parent_access(parent, course, db):
        raise parent_errors.ParentRoleRequired(parent.email, course.course_id)


def assert_not_parent(user: User, course: Course, db: Session) -> None:
    """Asserts that the provided user is already a parent in the provided course."""
    if check_parent_access(user, course, db):
        raise parent_errors.ParentRoleConflict(user.email, course.course_id)


def check_parent_of_student(parent: User, student: User, course: Course, db: Session) -> bool:
    return db.query(
        exists().where(
            (ParentAt.parent_email == parent.email) &
            (ParentAt.student_email == student.email) &
            (ParentAt.course_id == course.course_id)
        )
    ).scalar()


def assert_not_parent_of_student(parent: User, student: User, course: Course, db: Session) -> None:
    """Asserts that the provided user is not a parent of the student in the provided course."""
    if check_parent_of_student(parent, student, course, db):
        raise parent_errors.ParentOfStudentRoleConflict(parent.email, student.email, course.course_id)


def assert_parent_of_student(parent: User, student: User, course: Course, db: Session) -> None:
    """Asserts that the provided user is already parent of the student in the provided course."""
    if not check_parent_of_student(parent, student, course, db):
        raise parent_errors.ParentOfStudentRoleRequired(parent.email, student.email, course.course_id)


def invite_parent(parent: User, student: User, course: Course, db: Session) -> None:
    """Invite the provided parent to the provided course."""
    parent_of = ParentAt(
        parent_email=parent.email, 
        student_email=student.email,
        course_id=course.course_id
    )
    db.add(parent_of)


def get_students_parents(student: User, course: Course, db: Session) -> list[User]:
    """Get the list of parents observing the provided student within the provided course."""
    return (
        db.query(User)
        .join(ParentAt, ParentAt.parent_email == User.email)
        .filter(
            ParentAt.student_email == student.email,
            ParentAt.course_id == course.course_id
        )
        .all()
    )


def get_parents_children(parent: User, course: Course, db: Session) -> list[User]:
    """Get the list of students that the provided parent observes within the provided course."""

    return (
        db.query(User)
        .join(ParentAt, ParentAt.student_email == User.email)
        .filter(
            ParentAt.parent_email == parent.email,
            ParentAt.course_id == course.course_id
        )
        .all()
    )
