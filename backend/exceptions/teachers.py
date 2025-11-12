class TeacherError(Exception):
    """Base exception for teacher-related errors."""


class InstructorRoleRequired(TeacherError):
    """Exception raised for invalid email format."""

    def __init__(self, email: str, course_name: str) -> None:
        super().__init__(
            f"User {email} does not have the instructor access within the course {course_name}."
        )
