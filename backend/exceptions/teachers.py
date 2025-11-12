from exceptions.courses import RoleConflict

class TeacherError(Exception):
    """Base exception for teacher-related errors."""


class InstructorRoleRequired(TeacherError):
    """Exception raised when some random user want to access instructor functionality."""

    def __init__(self, email: str, course_name: str) -> None:
        super().__init__(
            f"User {email} does not have the instructor access within the course {course_name}."
        )

class TeacherRoleRequired(TeacherError):
    """Exception raised when some random user want to access teacher functionality."""

    def __init__(self, email: str, course_name: str) -> None:
        super().__init__(
            f"User {email} does not have not teacher nor instructor access within the course {course_name}."
        )

class TeacherRoleConflict(TeacherError, RoleConflict):
    """Exception raised when the teacher role conflict appears."""

    def __init__(self, email: str, course_id: str) -> None:
        super().__init__(f"User {email} is already teacher at the course {course_id}.")
