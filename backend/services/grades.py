from repo.grades import Grade
from repo.submissions import AssignmentSubmission
import exceptions.submissions as submission_errors
from repo.users import User
from sqlalchemy.orm import Session
import logging


class GradeService:
    """Service class for managing grades related operations."""

    logger = logging.getLogger("GradeService")

    def __init__(self, db: Session):
        self.db = db

    def update_submission_grade(
        self,
        submission: AssignmentSubmission,
        grade: int,
        comment: str | None,
        teacher: User,
    ) -> None:
        """Set the new grade for the submission."""
        self.logger.info(
            f"Updating grade for submission: course_id={submission.course_id}, assignment_id={submission.assignment_id}, student_email={submission.email}, grade={grade}, teacher_email={teacher.email}"
        )
        graded = (
            self.db.query(Grade)
            .filter(
                Grade.course_id == submission.course_id,
                Grade.assignment_id == submission.assignment_id,
                Grade.student_email == submission.email,
            )
            .first()
        )
        if not graded:
            self.logger.info("No existing grade found, creating a new one.")
            graded = Grade(
                course_id=submission.course_id,
                assignment_id=submission.assignment_id,
                student_email=submission.email,
                grade=grade,
                comment=comment,
                teacher_email=teacher.email,
            )
            self.db.add(graded)
            return
        graded.grade = grade
        graded.comment = comment
        graded.gradedby = teacher.email

    def get_submission_grade(self, submission: AssignmentSubmission) -> Grade:
        """Get the grade for the provided submission."""
        grade = (
            self.db.query(Grade)
            .filter(
                Grade.course_id == submission.course_id,
                Grade.assignment_id == submission.assignment_id,
                Grade.student_email == submission.email,
            )
            .first()
        )
        if not grade:
            self.logger.warning("Attempt to access non-existing grade for submission.")
            raise submission_errors.GradeNotFoundError(
                submission.course_id, submission.assignment_id, submission.email
            )
        return grade
