from repo.assignments import CourseAssignment
from repo.submissions import AssignmentSubmission
from repo.users import User
import exceptions.submissions as submission_errors
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging


class SubmissionService:
    """Service class for managing submission-related operations."""

    logger = logging.getLogger(__name__)

    def __init__(self, db: Session):
        self.db = db

    def get_submission(
        self, assignment: CourseAssignment, student: User
    ) -> AssignmentSubmission:
        """Get the submission by provided assignment and student."""
        submission = (
            self.db.query(AssignmentSubmission)
            .filter(
                AssignmentSubmission.course_id == assignment.course_id,
                AssignmentSubmission.assignment_id == assignment.assignment_id,
                AssignmentSubmission.email == student.email,
            )
            .first()
        )
        if not submission:
            self.logger.warning(
                f"Attempt to get non-existent submission for assignment {assignment.assignment_id} in course {assignment.course_id} by student {student.email}"
            )
            raise submission_errors.SubmissionNotFoundError(
                assignment.course_id, assignment.assignment_id, student.email
            )
        return submission

    def get_assignment_submissions(
        self, assignment: CourseAssignment
    ) -> list[AssignmentSubmission]:
        """Get the list of all submissions to the provided assignment."""
        return (
            self.db.query(AssignmentSubmission)
            .filter(
                AssignmentSubmission.course_id == assignment.course_id,
                AssignmentSubmission.assignment_id == assignment.assignment_id,
            )
            .all()
        )

    def create_submission(
        self, assignment: CourseAssignment, student: User, submission_text: str
    ) -> None:
        """Create an assignment submission."""
        self.logger.info(
            f"Creating submission for assignment {assignment.assignment_id} in course {assignment.course_id} by student {student.email}"
        )
        submission = AssignmentSubmission(
            course_id=assignment.course_id,
            assignment_id=assignment.assignment_id,
            email=student.email,
            submission_text=submission_text,
        )
        self.db.add(submission)

    def update_submission(
        self, submission: AssignmentSubmission, submission_text: str
    ) -> None:
        """Update the assignment submission."""
        self.logger.info(
            f"Updating submission for assignment {submission.assignment_id} in course {submission.course_id} by student {submission.email}"
        )
        submission.submission_text = submission_text
        submission.timemodified = datetime.now(tz=timezone.utc)
        self.db.flush()
