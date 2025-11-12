from exceptions import courses as course_errors
from sqlalchemy.orm import Session
from repo.courses import Course

def get_course(course_id: str, db: Session) -> Course:
    """Check whether a user with provided email exists in the system."""
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise course_errors.CourseNotFoundError(course_id)
    return course
