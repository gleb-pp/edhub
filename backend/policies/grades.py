from repo.grades import Grade
from repo.submissions import AssignmentSubmission
import exceptions.submissions as submission_errors
from sqlalchemy.orm import Session


class GradePolicy:
    """Policy class for handling grade-related assertions."""

    @staticmethod
    def assert_not_graded(submission: AssignmentSubmission, db: Session) -> None:
        """Assert that the provided submission is not graded yet."""
        grade = (
            db.query(Grade)
            .filter(
                Grade.course_id == submission.course_id,
                Grade.assignment_id == submission.assignment_id,
                Grade.student_email == submission.email,
            )
            .first()
        )
        if grade:
            raise submission_errors.SubmissionGradedError(
                submission.course_id, submission.assignment_id, submission.email
            )
