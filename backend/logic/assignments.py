from repo.assignments import CourseAssignment
from repo.sections import CourseSection
from repo.courses import Course
from repo.users import User
import exceptions.assignments as assignment_errors
from sqlalchemy.orm import Session

def get_section_assignments(section: CourseSection, db: Session) -> list[CourseAssignment]:
    """Get the list of course assignments within the provided section."""
    return db.query(CourseAssignment).filter(CourseAssignment.course_id == section.course_id, CourseAssignment.section_id == section.section_id).all()


def create_assignment(section: CourseSection, title: str, description: str, author: User, db: Session) -> CourseAssignment:
    """Create a new assignment within the provided course section."""
    assignment = CourseAssignment(
        course_id=section.course_id,
        section_id=section.section_id,
        author=author.email,
        title=title,
        description=description,
    )
    db.add(assignment)
    db.flush()
    return assignment


def get_assignment(course: Course, assignment_id: int, db: Session) -> CourseAssignment:
    """Get the assignment by the provided course and assignment_id."""
    assignment = db.query(CourseAssignment).filter(CourseAssignment.course_id == course.course_id, CourseAssignment.assignment_id == assignment_id).first()
    if not assignment:
        raise assignment_errors.AssignmentNotFoundError(course_id=course.course_id, assignment_id=assignment_id)
    return assignment


def get_course_assignments(course: Course, db: Session) -> list[CourseAssignment]:
    """Get the list of assignments within the provided course.

    Assignments are ordered by section_order, then by creation_date, old posts go first."""
    return (
        db.query(CourseAssignment)
        .join(
            CourseSection,
            (CourseSection.course_id == CourseAssignment.course_id)
            & (CourseSection.section_id == CourseAssignment.section_id)
        )
        .filter(CourseAssignment.course_id == course.course_id)
        .order_by(CourseSection.order.asc(), CourseAssignment.creation_time.asc())
        .all()
    )


def delete_assignment(assignment: CourseAssignment, db: Session) -> None:
    """Delete the provided course assignment."""
    db.delete(assignment)
