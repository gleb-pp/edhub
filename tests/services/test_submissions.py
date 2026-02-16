import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, UTC
from sqlalchemy.orm import Session

import src.exceptions.submissions as submission_errors
from src.repo import AssignmentSubmission, CourseAssignment, User
from src.services import SubmissionService


class TestSubmissionService:

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        return SubmissionService(mock_db)

    @pytest.fixture
    def mock_course_assignment(self):
        assignment = MagicMock(spec=CourseAssignment)
        assignment.course_id = 1
        assignment.assignment_id = 2
        return assignment

    @pytest.fixture
    def mock_student(self):
        student = MagicMock(spec=User)
        student.email = "student@test.com"
        return student

    @patch.object(SubmissionService.logger, "warning")
    def test_get_submission(self, mock_logger, service, mock_db, mock_course_assignment, mock_student):
        # случай, когда submission существует
        existing_submission = MagicMock(spec=AssignmentSubmission)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = existing_submission

        result = service.get_submission(mock_course_assignment, mock_student)
        assert result == existing_submission
        mock_db.query.assert_called_once_with(AssignmentSubmission)
        mock_query.filter.assert_called_once()
        mock_logger.assert_not_called()  # логгер не должен вызываться при успешном запросе

        # случай, когда submission не найден
        mock_filter.first.return_value = None
        with pytest.raises(submission_errors.SubmissionNotFoundError):
            service.get_submission(mock_course_assignment, mock_student)
        mock_logger.assert_called_once()  # логгер вызывается при ошибке

    @pytest.mark.parametrize("submissions_list", [
        ([MagicMock(spec=AssignmentSubmission), MagicMock(spec=AssignmentSubmission)]),
        ([])
    ])
    def test_get_assignment_submissions(self, service, mock_db, mock_course_assignment, submissions_list):
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = submissions_list

        result = service.get_assignment_submissions(mock_course_assignment)
        assert result == submissions_list
        mock_db.query.assert_called_once_with(AssignmentSubmission)
        mock_query.filter.assert_called_once()

    @patch.object(SubmissionService.logger, "info")
    def test_create_submission(self, mock_logger, service, mock_db, mock_course_assignment, mock_student):
        service.create_submission(mock_course_assignment, mock_student, "Test submission text")
        mock_db.add.assert_called_once()
        added_submission = mock_db.add.call_args[0][0]
        assert isinstance(added_submission, AssignmentSubmission)
        assert added_submission.course_id == mock_course_assignment.course_id
        assert added_submission.assignment_id == mock_course_assignment.assignment_id
        assert added_submission.email == mock_student.email
        assert added_submission.submission_text == "Test submission text"
        mock_logger.assert_called_once()

    @patch.object(SubmissionService.logger, "info")
    @patch("src.services.submissions.datetime")
    def test_update_submission_success(self, mock_datetime, mock_logger, service, mock_db):
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        submission = MagicMock(spec=AssignmentSubmission)
        submission.submission_text = "Old text"
        submission.timemodified = None

        service.update_submission(submission, "Updated text")
        assert submission.submission_text == "Updated text"
        assert submission.timemodified == mock_now
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(SubmissionService.logger, "info")
    @patch("src.services.submissions.datetime")
    def test_update_submission_empty_text(self, mock_datetime, mock_logger, service, mock_db):
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        submission = MagicMock(spec=AssignmentSubmission)
        submission.submission_text = "Old text"
        submission.timemodified = None

        service.update_submission(submission, "")
        assert submission.submission_text == ""
        assert submission.timemodified == mock_now
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()
