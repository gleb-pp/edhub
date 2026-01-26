class AssignmentError(Exception):
    """Base exception for assignment-related errors."""


class AssignmentNotFoundError(AssignmentError):
    """Exception raised when an assignment is not found."""

    def __init__(self, course_id: str, assignment_id: int) -> None:
        super().__init__(
            f"Assignments {assignment_id} does not exist in the course {course_id}."
        )
