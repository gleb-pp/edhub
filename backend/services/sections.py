from sqlalchemy.orm import Session
from repo.courses import Course
from repo.sections import CourseSection
import exceptions.sections as section_errors
from sqlalchemy import func
import logging


class SectionService:
    """Service class for managing course sections."""

    logger = logging.getLogger(__name__)

    def __init__(self, db: Session):
        self.db = db

    def get_course_sections(self, course: Course) -> list[CourseSection]:
        """Get the list of sections for the provided course."""
        return (
            self.db.query(CourseSection)
            .filter(CourseSection.course_id == course.course_id)
            .order_by(CourseSection.section_order)
            .all()
        )

    def get_section(self, course: Course, section_id: int) -> CourseSection:
        """Get the course section by the provided course and section_id."""
        section = (
            self.db.query(CourseSection)
            .filter(
                CourseSection.course_id == course.course_id,
                CourseSection.section_id == section_id,
            )
            .first()
        )
        if not section:
            self.logger.warning(
                f"Attempt to access non-existing section {section_id} in course {course.course_id}"
            )
            raise section_errors.SectionNotFoundError(section_id, course.course_id)
        return section

    def create_section(self, title: str, course: Course) -> CourseSection:
        """Create a new section within the course with provided id."""
        self.logger.info(
            f"Creating new section '{title}' for course {course.course_id}"
        )
        max_order = (
            self.db.query(func.max(CourseSection.section_order))
            .filter(CourseSection.course_id == course.course_id)
            .scalar()
        )
        new_order = (max_order or 0) + 1
        section = CourseSection(
            course_id=course.course_id, title=title, section_order=new_order
        )
        self.db.add(section)
        self.db.flush()
        return section

    def remove_section(self, section: CourseSection) -> None:
        """Delete the provided section from the course."""
        self.logger.info(
            f"Removing section {section.section_id} from course {section.course_id}"
        )
        section_count = (
            self.db.query(func.count(CourseSection.section_id))
            .filter(CourseSection.course_id == section.course_id)
            .scalar()
        )
        if section_count <= 1:
            raise section_errors.LastSectionDeleteError(
                section.section_id, section.course_id
            )
        self.db.delete(section)

    def change_section_order(self, course: Course, new_order: list[int]) -> None:
        """Set the new section order within the provided course by the list of ordered section_ids."""
        self.logger.info(
            f"Changing section order for course {course.course_id} to {new_order}"
        )
        sections = [sec.section_id for sec in self.get_course_sections(course)]
        if len(sections) != len(new_order) or set(sections) != set(new_order):
            self.logger.warning(
                f"Incorrect section order {new_order} for course {course.course_id}"
            )
            raise section_errors.IncorrectSectionOrderError

        for index, section_id in enumerate(new_order):
            self.db.query(CourseSection).filter(
                CourseSection.section_id == section_id,
                CourseSection.course_id == course.course_id,
            ).update({"section_order": index})
