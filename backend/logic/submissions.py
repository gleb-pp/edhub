from repo.assignments import CourseAssignment
from repo.submissions import AssignmentSubmission
from repo.users import User
import exceptions.submissions as submission_errors
from sqlalchemy.orm import Session
from datetime import datetime, timezone

def get_submission(assignment: CourseAssignment, student: User, db: Session) -> AssignmentSubmission:
    """Get the submission by provided assignment and student."""
    submission = db.query(AssignmentSubmission).filter(AssignmentSubmission.course_id == assignment.course_id, AssignmentSubmission.assignment_id == assignment.assignment_id, AssignmentSubmission.email == student.email).first()
    if not submission:
        raise submission_errors.SubmissionNotFoundError(assignment.course_id, assignment.assignment_id, student.email)
    return submission


def get_assignment_submissions(assignment: CourseAssignment, db: Session) -> list[AssignmentSubmission]:
    """Get the list of all submissions to the provided assignment."""
    return db.query(AssignmentSubmission).filter(AssignmentSubmission.course_id == assignment.course_id, AssignmentSubmission.assignment_id == assignment.assignment_id).all()


def create_submission(assignment: CourseAssignment, student: User, submission_text: str, db: Session) -> None:
    """Create an assignment submission."""
    submission = AssignmentSubmission(
        course_id=assignment.course_id,
        assignment_id=assignment.assignment_id,
        email=student.email,
        submission_text=submission_text,
    )
    db.add(submission)


def update_submission(submission: AssignmentSubmission, submission_text: str) -> None:
    """Update the assignment submission."""
    submission.submission_text = submission_text
    submission.timemodified = datetime.now(tz=timezone.utc)
