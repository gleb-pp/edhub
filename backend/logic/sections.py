from sqlalchemy.orm import Session
from repo.courses import Course
from repo.sections import CourseSection
import exceptions.sections as section_errors
from sqlalchemy import func

def get_course_sections(course: Course, db: Session) -> list[CourseSection]:
    """Get the list of sections for the provided course."""
    return db.query(CourseSection).filter(CourseSection.course_id == course.course_id).all()


def get_section(course: Course, section_id: int, db: Session) -> CourseSection:
    """Get the course section by the provided course and section_id."""
    section = db.query(CourseSection).filter(CourseSection.course_id == course.course_id, CourseSection.section_id == section_id).first()
    if not section:
        raise section_errors.SectionNotFoundError(section_id, course.course_id)
    return section


def create_section(title: str, course: Course, db: Session) -> CourseSection:
    """Create a new section within the course with provided id."""
    max_order = db.query(func.max(CourseSection.order)) \
                  .filter(CourseSection.course_id == course.course_id) \
                  .scalar()
    new_order = (max_order or 0) + 1
    section = CourseSection(
        course_id=course.course_id, 
        title=title,
        order=new_order
    )
    db.add(section)
    db.flush()
    return section


def remove_section(section: CourseSection, db: Session) -> None:
    """Delete the provided section from the course."""
    section_count = (
        db.query(func.count(CourseSection.section_id))
        .filter(CourseSection.course_id == section.course_id)
        .scalar()
    )
    if section_count <= 1:
        raise section_errors.LastSectionDeleteError(section.section_id, section.course_id)
    db.delete(section)


def change_section_order(course: Course, new_order: list[int], db: Session) -> None:
    """Set the new section order within the provided course by the list of ordered section_ids."""
    sections = [sec.section_id for sec in get_course_sections(course, db)]
    if len(sections) != new_order or set(sections) != set(new_order):
        raise section_errors.IncorrectSectionOrderError
    
    for index, section_id in enumerate(new_order):
        db.query(CourseSection).filter(
            CourseSection.section_id == section_id,
            CourseSection.course_id == course.course_id
        ).update({"order": index})
