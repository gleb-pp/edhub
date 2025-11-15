from exceptions import courses as course_errors
from sqlalchemy.orm import Session
from repo.courses import Course
from repo.users import User
from repo.personalization import PersonalCourseInfo
from sqlalchemy import exists

def get_course(course_id: str, db: Session) -> Course:
    """Check whether a user with provided email exists in the system."""
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise course_errors.CourseNotFoundError(course_id)
    return course


def get_available_courses(user: User, db: Session) -> list[Course]:
    """Get the list of courses available to user."""

    return (
        db.query(Course)
        .join(PersonalCourseInfo, PersonalCourseInfo.course_id == Course.course_id)
        .filter(PersonalCourseInfo.email == user.email)
        .order_by(PersonalCourseInfo.course_order.asc())
        .all()
    )


def assert_course_access(user: User, course: Course, db: Session) -> None:
    """Asserts that the provided user has an access to the provided course."""
    access = db.query(
        exists().where(
            (PersonalCourseInfo.email == user.email) &
            (PersonalCourseInfo.course_id == course.course_id)
        )
    ).scalar()
    if not access:
        raise course_errors.ParticipantRoleRequired(user.email, course.course_id)


def get_all_courses(db: Session) -> list[Course]:
    """Get the list of all courses within the platform."""

    return db.query(Course).all()


def create_course(title: str, organization: str | None, user: User, db: Session) -> Course:
    """Create the course with the provided parameters."""
    course = Course(title=title, organization=organization, instructor=user.email)
    db.add(course)
    db.flush()
    return course


def delete_course(course: Course, db: Session) -> None:
    """Delete the provided course from the system."""
    db.delete(course)
