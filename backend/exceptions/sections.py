class SectionError(Exception):
    """Base exception for course-related errors."""


class SectionNotFoundError(SectionError):
    """Exception raised when a section is not found."""

    def __init__(self, section_id: int, course_id: str) -> None:
        super().__init__(f"Section {section_id} does not exist in the course {course_id}.")


class LastSectionDeleteError(SectionError):
    """Exception raised when trying to remove the last section."""

    def __init__(self, section_id: int, course_id: str) -> None:
        super().__init__(f"Cannot remove the section {section_id} since is is the last one in the course {course_id}.")


class IncorrectSectionOrderError(SectionError):
    """Exception raised when trying to insert incorrect section order to change."""

    def __init__(self) -> None:
        super().__init__("New list of sections passed does not match with the original one.")
