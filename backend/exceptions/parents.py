from exceptions.courses import RoleConflict

class ParentError(Exception):
    """Base exception for parent-related errors."""

class ParentRoleConflict(ParentError, RoleConflict):
    """Exception raised when the parent role conflict appears."""

    def __init__(self, email: str, course_id: str) -> None:
        super().__init__(f"User {email} is already parent at the course {course_id}.")

class ParentOfStudentRoleConflict(ParentError, RoleConflict):
    """Exception raised when the parent role conflict appears."""

    def __init__(self, parent: str, student: str, course_id: str) -> None:
        super().__init__(f"User {parent} is already parent of student {student} at the course {course_id}.")


class ParentOfStudentRoleRequired(ParentError):
    """Exception raised when some random user want to access parent functionality."""

    def __init__(self, parent: str, student: str, course_id: str) -> None:
        super().__init__(
            f"User {parent} is not a parent of student {student} at the course {course_id}."
        )


class ParentRoleRequired(ParentError):
    """Exception raised when some random user want to access parent functionality."""

    def __init__(self, parent: str, course_id: str) -> None:
        super().__init__(
            f"User {parent} is not a parent at the course {course_id}."
        )
