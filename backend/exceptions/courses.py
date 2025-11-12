class CourseError(Exception):
    """Base exception for course-related errors."""

class CourseNotFoundError(CourseError):
    """Exception raised when a course is not found."""

    def __init__(self, course_id: str) -> None:
        super().__init__(f"Course {course_id} does not exist.")

class ParticipantRoleRequired(CourseError):
    """Exception raised when some random user accesses the course."""

    def __init__(self, email: str, course_id: str) -> None:
        super().__init__(f"User {email} is not a participant of a course {course_id}.")
