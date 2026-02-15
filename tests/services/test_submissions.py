from unittest.mock import MagicMock, patch
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

import src.exceptions.submissions as submission_errors
from src.services import SubmissionService
from src.repo import CourseAssignment, AssignmentSubmission, User


class TestSubmissionService:

    def test_get_submission_success(self):
        mock_db = MagicMock(spec=Session)
        mock_assignment = MagicMock(spec=CourseAssignment)
        mock_assignment.course_id = 1
        mock_assignment.assignment_id = 2
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        
        expected_submission = MagicMock(spec=AssignmentSubmission)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = expected_submission
        
        service = SubmissionService(mock_db)
        result = service.get_submission(mock_assignment, mock_student)
        
        assert result == expected_submission
        mock_db.query.assert_called_once_with(AssignmentSubmission)
        mock_query.filter.assert_called_once()

    @patch.object(SubmissionService.logger, 'warning')
    def test_get_submission_not_found(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_assignment = MagicMock(spec=CourseAssignment)
        mock_assignment.course_id = 1
        mock_assignment.assignment_id = 2
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        service = SubmissionService(mock_db)
        
        with pytest.raises(submission_errors.SubmissionNotFoundError) as exc_info:
            service.get_submission(mock_assignment, mock_student)
        
        assert "1" in str(exc_info.value)
        assert "2" in str(exc_info.value)
        assert "student@test.com" in str(exc_info.value)
        mock_logger.assert_called_once()

    def test_get_assignment_submissions_success(self):
        mock_db = MagicMock(spec=Session)
        mock_assignment = MagicMock(spec=CourseAssignment)
        mock_assignment.course_id = 1
        mock_assignment.assignment_id = 2
        
        expected_submissions = [MagicMock(spec=AssignmentSubmission), MagicMock(spec=AssignmentSubmission)]
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = expected_submissions
        
        service = SubmissionService(mock_db)
        result = service.get_assignment_submissions(mock_assignment)
        
        assert result == expected_submissions
        mock_db.query.assert_called_once_with(AssignmentSubmission)
        mock_query.filter.assert_called_once()

    def test_get_assignment_submissions_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_assignment = MagicMock(spec=CourseAssignment)
        mock_assignment.course_id = 1
        mock_assignment.assignment_id = 2
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.all.return_value = []
        
        service = SubmissionService(mock_db)
        result = service.get_assignment_submissions(mock_assignment)
        
        assert result == []

    @patch.object(SubmissionService.logger, 'info')
    def test_create_submission_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_assignment = MagicMock(spec=CourseAssignment)
        mock_assignment.course_id = 1
        mock_assignment.assignment_id = 2
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        
        service = SubmissionService(mock_db)
        service.create_submission(mock_assignment, mock_student, "Test submission text")
        
        mock_db.add.assert_called_once()
        added_submission = mock_db.add.call_args[0][0]
        assert isinstance(added_submission, AssignmentSubmission)
        assert added_submission.course_id == mock_assignment.course_id
        assert added_submission.assignment_id == mock_assignment.assignment_id
        assert added_submission.email == mock_student.email
        assert added_submission.submission_text == "Test submission text"
        mock_logger.assert_called_once()

    def test_create_submission_empty_text(self):
        mock_db = MagicMock(spec=Session)
        mock_assignment = MagicMock(spec=CourseAssignment)
        mock_assignment.course_id = 1
        mock_assignment.assignment_id = 2
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        
        service = SubmissionService(mock_db)
        service.create_submission(mock_assignment, mock_student, "")
        
        added_submission = mock_db.add.call_args[0][0]
        assert added_submission.submission_text == ""

    @patch.object(SubmissionService.logger, 'info')
    @patch('src.services.submissions.datetime')
    def test_update_submission_success(self, mock_datetime, mock_logger):
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now
        
        mock_db = MagicMock(spec=Session)
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.course_id = 1
        mock_submission.assignment_id = 2
        mock_submission.email = "student@test.com"
        mock_submission.submission_text = "Old text"
        mock_submission.timemodified = None
        
        service = SubmissionService(mock_db)
        service.update_submission(mock_submission, "Updated submission text")
        
        assert mock_submission.submission_text == "Updated submission text"
        assert mock_submission.timemodified == mock_now
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(SubmissionService.logger, 'info')
    @patch('src.services.submissions.datetime')
    def test_update_submission_empty_text(self, mock_datetime, mock_logger):
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now
        
        mock_db = MagicMock(spec=Session)
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.submission_text = "Old text"
        mock_submission.timemodified = None
        
        service = SubmissionService(mock_db)
        service.update_submission(mock_submission, "")
        
        assert mock_submission.submission_text == ""
        assert mock_submission.timemodified == mock_now
