from typing import cast
from unittest.mock import MagicMock

import pytest

from src.exceptions.courses import ParticipantRoleRequiredError
from src.policies.courses import CoursePolicy
from src.repo.courses import Course
from src.repo.users import User


class DummyUser:
    def __init__(self):
        self.email = "user@gmail.com"


class DummyCourse:
    def __init__(self):
        self.course_id = 1


class TestCoursePolicy:

    def test_assert_course_access_success(self):
        db = MagicMock()
        db.query().scalar.return_value = True
        CoursePolicy.assert_course_access(cast("User", DummyUser()), cast("Course", DummyCourse()), db)

    def test_assert_course_access_fail(self):
        db = MagicMock()
        db.query().scalar.return_value = False
        with pytest.raises(ParticipantRoleRequiredError):
            CoursePolicy.assert_course_access(cast("User", DummyUser()), cast("Course", DummyCourse()), db)
