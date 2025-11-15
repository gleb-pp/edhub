from repo.grades import Grade
from repo.submissions import AssignmentSubmission
import exceptions.submissions as submission_errors
from repo.users import User
from sqlalchemy.orm import Session


def update_submission_grade(submission: AssignmentSubmission, grade: int, comment: str | None, teacher: User, db: Session) -> None:
    """Set the new grade for the submission."""
    graded = db.query(Grade).filter(Grade.course_id == submission.course_id, Grade.assignment_id == submission.assignment_id, Grade.student_email == submission.email).first()
    if not graded:
        graded = Grade(
            course_id=submission.course_id,
            assignment_id=submission.assignment_id,
            student_email=submission.email,
            grade=grade,
            comment=comment,
            teacher_email=teacher.email
        )
        db.add(graded)
        return
    graded.grade = grade
    graded.comment = comment
    graded.gradedby = teacher.email


def assert_not_graded(submission: AssignmentSubmission, db: Session) -> None:
    """Assert that the provided submission is not graded yet."""
    grade = db.query(Grade).filter(Grade.course_id == submission.course_id, Grade.assignment_id == submission.assignment_id, Grade.student_email == submission.email).first()
    if grade:
        raise submission_errors.SubmissionGradedError(submission.course_id, submission.assignment_id, submission.email)


def get_submission_grade(submission: AssignmentSubmission, db: Session) -> Grade:
    """Get the grade for the provided submission."""
    grade = db.query(Grade).filter(Grade.course_id == submission.course_id, Grade.assignment_id == submission.assignment_id, Grade.student_email == submission.email).first()
    if not grade:
        raise submission_errors.GradeNotFoundError(submission.course_id, submission.assignment_id, submission.email)
    return grade
