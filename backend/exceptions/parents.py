from exceptions.courses import RoleConflict

class ParentError(Exception):
    """Base exception for parent-related errors."""

class ParentRoleConflict(ParentError, RoleConflict):
    """Exception raised when the parent role conflict appears."""

    def __init__(self, email: str, course_id: str) -> None:
        super().__init__(f"User {email} is already parent at the course {course_id}.")
