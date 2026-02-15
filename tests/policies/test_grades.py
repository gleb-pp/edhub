from unittest.mock import MagicMock

import pytest

from src.exceptions.submissions import SubmissionGradedError
from src.policies import GradePolicy
from src.repo.submissions import AssignmentSubmission


class TestGradePolicy:

    def test_assert_not_graded_success(self):
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.course_id = 1
        mock_submission.assignment_id = 2
        mock_submission.email = "student@test.com"
        
        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = None

        GradePolicy.assert_not_graded(mock_submission, mock_db)

    def test_assert_not_graded_fail(self):
        mock_submission = MagicMock(spec=AssignmentSubmission)
        mock_submission.course_id = 1
        mock_submission.assignment_id = 2
        mock_submission.email = "student@test.com"
        
        mock_db = MagicMock()
        mock_db.query().filter().first.return_value = object()

        with pytest.raises(SubmissionGradedError):
            GradePolicy.assert_not_graded(mock_submission, mock_db)
