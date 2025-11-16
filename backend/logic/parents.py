from repo.users import User
from repo.courses import Course
from repo.parents import ParentAt
from sqlalchemy.orm import Session
from sqlalchemy import exists
import exceptions.parents as parent_errors
import logic.courses as course_logic
import logic.teachers as teacher_logic


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


def remove_parent_student(parent: User, student: User, course: Course, db: Session) -> None:
    """Remove the provided parent from observing the provided student within the provided course."""
    db.delete(
        db.query(ParentAt).filter(
            ParentAt.parent_email == parent.email,
            ParentAt.student_email == student.email,
            ParentAt.course_id == course.course_id
        ).first()
    )
    db.flush()


def remove_parent(parent: User, course: Course, db: Session) -> None:
    """Remove the provided parent from the provided course."""
    db.delete(
        db.query(ParentAt).filter(
            ParentAt.parent_email == parent.email,
            ParentAt.course_id == course.course_id
        ).first()
    )


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


def assert_access_to_parent(parent: User, user: User, course: Course, db: Session) -> None:
    """Asserts that the provided user has access to the provided parent."""
    course_logic.assert_course_access(user, course, db)
    assert_parent_access(parent, course, db)
    if not (
        teacher_logic.check_teacher_access(user, course, db) or
        user.email == parent.email or
        user.isadmin
    ):
        raise parent_errors.NoAccessToParentInfo(parent.email, user.email, course.id)
