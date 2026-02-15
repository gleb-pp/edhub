from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.submissions as submission_errors
from src.services import GradeService
from src.repo import Grade, AssignmentSubmission, User


class TestGradeService:

    @patch.object(GradeService.logger, 'info')
    def test_update_submission_grade_create_new(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.course_id = 1
        mock_submission.assignment_id = 2
        mock_submission.email = "student@test.com"
        
        mock_teacher = MagicMock(spec=User)
        mock_teacher.email = "teacher@test.com"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        service = GradeService(mock_db)
        service.update_submission_grade(mock_submission, 85, "Good job!", mock_teacher)
        
        mock_db.query.assert_called_once_with(Grade)
        mock_query.filter.assert_called_once()
        mock_db.add.assert_called_once()
        
        added_grade = mock_db.add.call_args[0][0]
        assert isinstance(added_grade, Grade)
        assert added_grade.course_id == mock_submission.course_id
        assert added_grade.assignment_id == mock_submission.assignment_id
        assert added_grade.student_email == mock_submission.email
        assert added_grade.grade == 85
        assert added_grade.comment == "Good job!"
        assert added_grade.teacher_email == mock_teacher.email
        
        assert mock_logger.call_count == 2

    @patch.object(GradeService.logger, 'info')
    def test_update_submission_grade_create_new_without_comment(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.course_id = 1
        mock_submission.assignment_id = 2
        mock_submission.email = "student@test.com"
        
        mock_teacher = MagicMock(spec=User)
        mock_teacher.email = "teacher@test.com"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        service = GradeService(mock_db)
        service.update_submission_grade(mock_submission, 90, None, mock_teacher)
        
        mock_db.add.assert_called_once()
        added_grade = mock_db.add.call_args[0][0]
        assert added_grade.grade == 90
        assert added_grade.comment is None

    @patch.object(GradeService.logger, 'info')
    def test_update_submission_grade_update_existing(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.course_id = 1
        mock_submission.assignment_id = 2
        mock_submission.email = "student@test.com"
        
        mock_teacher = MagicMock(spec=User)
        mock_teacher.email = "teacher@test.com"
        
        mock_existing_grade = MagicMock(spec=Grade)
        mock_existing_grade.grade = 70
        mock_existing_grade.comment = "Old comment"
        mock_existing_grade.teacher_email = "old_teacher@test.com"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_existing_grade
        
        service = GradeService(mock_db)
        service.update_submission_grade(mock_submission, 95, "Much better!", mock_teacher)
        
        mock_db.query.assert_called_once_with(Grade)
        mock_query.filter.assert_called_once()
        mock_db.add.assert_not_called()
        
        assert mock_existing_grade.grade == 95
        assert mock_existing_grade.comment == "Much better!"
        assert mock_existing_grade.teacher_email == mock_teacher.email
        
        mock_logger.assert_called_once()

    @patch.object(GradeService.logger, 'info')
    def test_update_submission_grade_update_existing_remove_comment(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.course_id = 1
        mock_submission.assignment_id = 2
        mock_submission.email = "student@test.com"
        
        mock_teacher = MagicMock(spec=User)
        mock_teacher.email = "teacher@test.com"
        
        mock_existing_grade = MagicMock(spec=Grade)
        mock_existing_grade.grade = 70
        mock_existing_grade.comment = "Old comment"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_existing_grade
        
        service = GradeService(mock_db)
        service.update_submission_grade(mock_submission, 100, None, mock_teacher)
        
        assert mock_existing_grade.grade == 100
        assert mock_existing_grade.comment is None

    def test_get_submission_grade_success(self):
        mock_db = MagicMock(spec=Session)
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.course_id = 1
        mock_submission.assignment_id = 2
        mock_submission.email = "student@test.com"
        
        expected_grade = MagicMock(spec=Grade)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = expected_grade
        
        service = GradeService(mock_db)
        result = service.get_submission_grade(mock_submission)
        
        assert result == expected_grade
        mock_db.query.assert_called_once_with(Grade)
        mock_query.filter.assert_called_once()

    @patch.object(GradeService.logger, 'warning')
    def test_get_submission_grade_not_found(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.course_id = 1
        mock_submission.assignment_id = 2
        mock_submission.email = "student@test.com"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        service = GradeService(mock_db)
        
        with pytest.raises(submission_errors.GradeNotFoundError) as exc_info:
            service.get_submission_grade(mock_submission)
        
        assert "1" in str(exc_info.value) or "1" in str(exc_info.value.__dict__)
        assert "2" in str(exc_info.value) or "2" in str(exc_info.value.__dict__)
        assert "student@test.com" in str(exc_info.value) or "student@test.com" in str(exc_info.value.__dict__)
        mock_logger.assert_called_once()
