from repo.assignments import CourseAssignment
from repo.sections import CourseSection
from sqlalchemy.orm import Session

def get_section_assignments(section: CourseSection, db: Session) -> list[CourseAssignment]:
    """Get the list of course assignments within the provided section."""
    return db.query(CourseAssignment).filter(CourseAssignment.course_id == section.course_id, CourseAssignment.section_id == section.section_id).all()
