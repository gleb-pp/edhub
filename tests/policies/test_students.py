from src.repo.courses import Course
import pytest
from typing import cast
from unittest.mock import MagicMock, patch
from src.policies.students import StudentPolicy
from src.exceptions.students import (
    StudentRoleRequiredError,
    StudentRoleConflictError,
    NoAccessToStudentInfoError,
)
from src.repo.users import User


class DummyUser:
    def __init__(self, email="user@gmail.com"):
        self.email = email
        self.isadmin = False


class DummyCourse:
    course_id = 1
    title = "Course"
    id = 1


class TestStudentPolicy:

    def test_assert_student_access_fail(self):
        db = MagicMock()
        db.query().scalar.return_value = False

        with pytest.raises(StudentRoleRequiredError):
            StudentPolicy.assert_student_access(cast(User, DummyUser()), cast(Course, DummyCourse()), db)

    def test_assert_not_student_conflict(self):
        db = MagicMock()
        db.query().scalar.return_value = True

        with pytest.raises(StudentRoleConflictError):
            StudentPolicy.assert_not_student(cast(User, DummyUser()), cast(Course, DummyCourse()), db)

    @patch("src.policies.students.CoursePolicy.assert_course_access")
    @patch("src.policies.students.TeacherPolicy.check_teacher_access")
    @patch("src.policies.students.ParentPolicy.check_parent_of_student")
    def test_access_to_student_denied(
        self, parent_mock, teacher_mock, course_mock
    ):
        teacher_mock.return_value = False
        parent_mock.return_value = False

        db = MagicMock()
        db.query().scalar.return_value = True

        with pytest.raises(NoAccessToStudentInfoError):
            StudentPolicy.assert_access_to_student(
                cast(User, DummyUser("student@test.com")),
                cast(User, DummyUser("other@test.com")),
                cast(Course, DummyCourse()),
                db,
            )
