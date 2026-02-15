class SubmissionError(Exception):
    """Base exception for submission-related errors."""


class SubmissionNotFoundError(SubmissionError):
    """Exception raised when an assignment is not found."""

    def __init__(self, course_id: str, assignment_id: int, student_email: str) -> None:
        super().__init__(
            f"Submission of student {student_email} to the assignment {assignment_id} does not exist in the course {course_id}.",
        )


class SubmissionGradedError(SubmissionError):
    """Exception raised when the submission is already graded."""

    def __init__(self, course_id: str, assignment_id: int, student_email: str) -> None:
        super().__init__(
            f"Submission of student {student_email} to the assignment {assignment_id} withing the course {course_id} is already graded.",
        )


class GradeNotFoundError(SubmissionError):
    """Exception raised when the submission grade is not found."""

    def __init__(self, course_id: str, assignment_id: int, student_email: str) -> None:
        super().__init__(
            f"Submission of student {student_email} to the assignment {assignment_id} withing the course {course_id} is not graded.",
        )
