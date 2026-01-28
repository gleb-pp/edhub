from repo.materials import CourseMaterial
from repo.sections import CourseSection
from repo.courses import Course
from repo.users import User
import exceptions.materials as material_errors
from sqlalchemy.orm import Session
import logging


class MaterialService:
    """Service for managing course materials."""

    logger = logging.getLogger(__name__)

    def __init__(self, db: Session):
        self.db = db

    def get_section_materials(self, section: CourseSection) -> list[CourseMaterial]:
        """Get the list of course materials within the provided section."""
        return (
            self.db.query(CourseMaterial)
            .filter(
                CourseMaterial.course_id == section.course_id,
                CourseMaterial.section_id == section.section_id,
            )
            .all()
        )

    def create_material(
        self, section: CourseSection, title: str, description: str, author: User
    ) -> CourseMaterial:
        """Create a new material within the provided course section."""
        self.logger.info(
            f"Creating material '{title}' in section {section.section_id} of course {section.course_id} by author {author.email}"
        )
        material = CourseMaterial(
            course_id=section.course_id,
            section_id=section.section_id,
            author=author.email,
            title=title,
            description=description,
        )
        self.db.add(material)
        self.db.flush()
        return material

    def get_material(self, course: Course, material_id: int) -> CourseMaterial:
        """Get the material by the provided course and material_id."""
        material = (
            self.db.query(CourseMaterial)
            .filter(
                CourseMaterial.course_id == course.course_id,
                CourseMaterial.material_id == material_id,
            )
            .first()
        )
        if not material:
            self.logger.warning(
                f"Attempt to access non-existing material {material_id} in course {course.course_id}"
            )
            raise material_errors.MaterialNotFoundError(
                course_id=course.course_id, material_id=material_id
            )
        return material

    def delete_material(self, material: CourseMaterial) -> None:
        """Delete the provided course material."""
        self.logger.info(
            f"Deleting material {material.material_id} from course {material.course_id}"
        )
        self.db.delete(material)
