from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from src.exceptions.parents import (
    NoAccessToParentInfoError,
    ParentOfStudentRoleConflictError,
    ParentOfStudentRoleRequiredError,
    ParentRoleConflictError,
    ParentRoleRequiredError,
)
from src.policies.parents import ParentPolicy
from src.repo.courses import Course
from src.repo.users import User


class DummyUser:
    def __init__(self, email="user@gmail.com"):
        self.email = email
        self.isadmin = False


class DummyCourse:
    course_id = 1


class TestParentPolicy:

    def test_assert_parent_access_success(self):
        db = MagicMock()
        db.query().scalar.return_value = True
        ParentPolicy.assert_parent_access(cast("User", DummyUser()), cast("Course", DummyCourse()), db)

    def test_assert_parent_access_fail(self):
        db = MagicMock()
        db.query().scalar.return_value = False

        with pytest.raises(ParentRoleRequiredError):
            ParentPolicy.assert_parent_access(cast("User", DummyUser()), cast("Course", DummyCourse()), db)

    def test_assert_not_parent_fail(self):
        db = MagicMock()
        db.query().scalar.return_value = True

        with pytest.raises(ParentRoleConflictError):
            ParentPolicy.assert_not_parent(cast("User", DummyUser()), cast("Course", DummyCourse()), db)

    def test_assert_parent_of_student_required(self):
        db = MagicMock()
        db.query().scalar.return_value = False

        with pytest.raises(ParentOfStudentRoleRequiredError):
            ParentPolicy.assert_parent_of_student(
                cast("User", DummyUser()), cast("User", DummyUser("s@test.com")), cast("Course", DummyCourse()), db,
            )

    def test_assert_not_parent_of_student(self):
        db = MagicMock()
        db.query().scalar.return_value = True

        with pytest.raises(ParentOfStudentRoleConflictError):
            ParentPolicy.assert_not_parent_of_student(
                cast("User", DummyUser()), cast("User", DummyUser("s@test.com")), cast("Course", DummyCourse()), db,
            )

    @patch("src.policies.parents.CoursePolicy.assert_course_access")
    @patch("src.policies.parents.TeacherPolicy.check_teacher_access")
    def test_assert_access_to_parent_denied(self, teacher_mock, course_mock):
        teacher_mock.return_value = False

        db = MagicMock()
        db.query().scalar.return_value = True

        with pytest.raises(NoAccessToParentInfoError):
            ParentPolicy.assert_access_to_parent(
                cast("User", DummyUser("parent@test.com")),
                cast("User", DummyUser("other@test.com")),
                cast("Course", DummyCourse()),
                db,
            )
