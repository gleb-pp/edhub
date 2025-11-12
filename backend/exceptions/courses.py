class CourseError(Exception):
    """Base exception for course-related errors."""

class CourseNotFoundError(CourseError):
    """Exception raised when a course is not found."""

    def __init__(self, course_id: str) -> None:
        super().__init__(f"Course {course_id} does not exist.")
