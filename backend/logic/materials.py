from repo.materials import CourseMaterial
from repo.sections import CourseSection
from repo.courses import Course
from repo.users import User
import exceptions.materials as material_errors
from sqlalchemy.orm import Session

def get_section_materials(section: CourseSection, db: Session) -> list[CourseMaterial]:
    """Get the list of course materials within the provided section."""
    return db.query(CourseMaterial).filter(CourseMaterial.course_id == section.course_id, CourseMaterial.section_id == section.section_id).all()


def create_material(section: CourseSection, title: str, description: str, author: User, db: Session) -> CourseMaterial:
    """Create a new material within the provided course section."""
    material = CourseMaterial(
        course_id=section.course_id,
        section_id=section.section_id,
        author=author.email,
        title=title,
        description=description,
    )
    db.add(material)
    db.flush()
    return material


def get_material(course: Course, material_id: int, db: Session) -> CourseMaterial:
    """Get the material by the provided course and material_id."""
    material = db.query(CourseMaterial).filter(CourseMaterial.course_id == course.course_id, CourseMaterial.material_id == material_id).first()
    if not material:
        raise material_errors.MaterialNotFoundError(course_id=course.course_id, material_id=material_id)
    return material


def delete_material(material: CourseMaterial, db: Session) -> None:
    """Delete the provided course material."""
    db.delete(material)
