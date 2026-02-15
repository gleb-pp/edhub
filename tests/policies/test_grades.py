from typing import cast
from unittest.mock import MagicMock

import pytest

from src.exceptions.submissions import SubmissionGradedError
from src.policies.grades import GradePolicy
from src.repo.submissions import AssignmentSubmission


class DummySubmission:
    course_id = 1
    assignment_id = 2
    email = "student@test.com"


class TestGradePolicy:

    def test_assert_not_graded_success(self):
        db = MagicMock()
        db.query().filter().first.return_value = None

        GradePolicy.assert_not_graded(cast("AssignmentSubmission", DummySubmission()), db)

    def test_assert_not_graded_fail(self):
        db = MagicMock()
        db.query().filter().first.return_value = object()

        with pytest.raises(SubmissionGradedError):
            GradePolicy.assert_not_graded(cast("AssignmentSubmission", DummySubmission()), db)
