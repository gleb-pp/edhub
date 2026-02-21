from src.exceptions.courses import RoleConflictError


class StudentError(Exception):
    """Base exception for student-related errors."""


class StudentRoleConflictError(StudentError, RoleConflictError):
    """Exception raised when the student role conflict appears."""

    def __init__(self, email: str, course_id: str) -> None:
        super().__init__(
            f"User {email} is already student at the course {course_id}.",
        )


class StudentRoleRequiredError(StudentError):
    """Exception raised when some random user want to access student functionality."""

    def __init__(self, email: str, course_title: str) -> None:
        super().__init__(
            f"User {email} is not a student at the course {course_title}.",
        )


class NoAccessToStudentInfoError(StudentError):
    """Exception raised when some random user want to access the student information."""

    def __init__(self, student_email: str, user_email: str, course_id: str) -> None:
        super().__init__(
            f"User {user_email} has no access to the student {student_email} within the course {course_id}.",
        )
