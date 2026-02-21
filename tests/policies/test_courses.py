from unittest.mock import MagicMock

import pytest

from src.exceptions.courses import ParticipantRoleRequiredError
from src.policies import CoursePolicy
from src.repo.courses import Course
from src.repo.users import User


class TestCoursePolicy:
    """Tests for the CoursePolicy class."""

    def test_assert_course_access_success(self) -> None:
        """Test that assert_course_access does not raise an error for a user with access to the course."""
        mock_user = MagicMock(spec=User)
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        CoursePolicy.assert_course_access(mock_user, mock_course, mock_db)

    def test_assert_course_access_fail(self) -> None:
        """Test that assert_course_access raises a ParticipantRoleRequiredError for a user without access to the course."""
        mock_user = MagicMock(spec=User)
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = False

        with pytest.raises(ParticipantRoleRequiredError):
            CoursePolicy.assert_course_access(mock_user, mock_course, mock_db)
