from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.submissions as submission_errors
from src.repo import AssignmentSubmission, Grade, User
from src.services import GradeService


class TestGradeService:
    """Unit tests for GradeService methods."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Fixture for a mocked database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db: MagicMock) -> GradeService:
        """Fixture for the GradeService instance with a mocked database."""
        return GradeService(mock_db)

    @pytest.fixture
    def mock_submission(self) -> MagicMock:
        """Fixture for a mocked AssignmentSubmission instance."""
        submission = MagicMock(spec=AssignmentSubmission)
        submission.course_id = 1
        submission.assignment_id = 2
        submission.email = "student@test.com"
        return submission

    @pytest.fixture
    def mock_teacher(self) -> MagicMock:
        """Fixture for a mocked User instance representing a teacher."""
        teacher = MagicMock(spec=User)
        teacher.email = "teacher@test.com"
        return teacher

    @pytest.mark.parametrize(
        ("existing_grade", "new_grade", "comment"),
        [
            (None, 85, "Good job!"),
            (None, 90, None),
            (MagicMock(spec=Grade), 95, "Much better!"),
            (MagicMock(spec=Grade), 100, None),
        ],
    )
    @patch.object(GradeService.logger, "info")
    def test_update_submission_grade(
        self,
        mock_logger: MagicMock,
        service: GradeService,
        mock_db: MagicMock,
        mock_submission: MagicMock,
        mock_teacher: MagicMock,
        existing_grade: MagicMock | None,
        new_grade: int,
        comment: str | None,
    ) -> None:
        """Test that a submission grade is updated successfully."""
        if existing_grade:
            existing_grade.grade = 70
            existing_grade.comment = "Old comment"
            existing_grade.teacher_email = "old_teacher@test.com"

        mock_db.query.return_value.filter.return_value.first.return_value = existing_grade

        service.update_submission_grade(
            mock_submission,
            new_grade,
            comment,
            mock_teacher,
        )

        mock_db.query.assert_called_once_with(Grade)

        if existing_grade is None:
            mock_db.add.assert_called_once()
            added_grade = mock_db.add.call_args[0][0]
            assert isinstance(added_grade, Grade)
            assert added_grade.course_id == mock_submission.course_id
            assert added_grade.assignment_id == mock_submission.assignment_id
            assert added_grade.student_email == mock_submission.email
            assert added_grade.grade == new_grade
            assert added_grade.comment == comment
            assert added_grade.teacher_email == mock_teacher.email
        else:
            mock_db.add.assert_not_called()
            assert existing_grade.grade == new_grade
            assert existing_grade.comment == comment
            assert existing_grade.teacher_email == mock_teacher.email

    @pytest.mark.parametrize(
        ("db_result", "should_raise"),
        [
            (MagicMock(spec=Grade), False),
            (None, True),
        ],
    )
    @patch.object(GradeService.logger, "warning")
    def test_get_submission_grade(
        self,
        mock_logger: MagicMock,
        service: GradeService,
        mock_db: MagicMock,
        mock_submission: MagicMock,
        db_result: MagicMock | None,
        should_raise: bool,
    ) -> None:
        """Test that a submission grade is retrieved successfully."""
        mock_db.query.return_value.filter.return_value.first.return_value = db_result

        if should_raise:
            with pytest.raises(submission_errors.GradeNotFoundError) as exc_info:
                service.get_submission_grade(mock_submission)
            error_text = str(exc_info.value)
            assert "1" in error_text
            assert "2" in error_text
            assert "student@test.com" in error_text
            mock_logger.assert_called_once()
        else:
            result = service.get_submission_grade(mock_submission)
            assert result == db_result
            mock_db.query.assert_called_once_with(Grade)
