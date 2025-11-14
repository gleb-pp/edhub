from repo.materials import CourseMaterial
from repo.sections import CourseSection
from sqlalchemy.orm import Session

def get_section_materials(section: CourseSection, db: Session) -> list[CourseMaterial]:
    """Get the list of course materials within the provided section."""
    return db.query(CourseMaterial).filter(CourseMaterial.course_id == section.course_id, CourseMaterial.section_id == section.section_id).all()
