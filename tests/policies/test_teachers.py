import pytest
from unittest.mock import MagicMock
from typing import cast
from src.policies.teachers import TeacherPolicy
from src.exceptions.teachers import (
    InstructorRoleRequiredError,
    TeacherRoleRequiredError,
    TeacherRoleConflictError,
)
from src.repo.courses import Course
from src.repo.users import User


class DummyUser:
    def __init__(self, email="user@gmail.com"):
        self.email = email


class DummyCourse:
    def __init__(self, instructor="i@test.com"):
        self.instructor = instructor
        self.course_id = 1
        self.name = "Course"


class TestTeacherPolicy:

    def test_assert_instructor_access_fail(self):
        db = MagicMock()
        db.query().scalar.return_value = False

        with pytest.raises(InstructorRoleRequiredError):
            TeacherPolicy.assert_instructor_access(cast(User, DummyUser()), cast(Course, DummyCourse()), db)

    def test_assert_teacher_access_fail(self):
        db = MagicMock()
        db.query().scalar.return_value = False

        with pytest.raises(TeacherRoleRequiredError):
            TeacherPolicy.assert_teacher_access(cast(User, DummyUser()), cast(Course, DummyCourse()), db)

    def test_assert_not_teacher_conflict(self):
        db = MagicMock()
        db.query().scalar.return_value = True

        with pytest.raises(TeacherRoleConflictError):
            TeacherPolicy.assert_not_teacher(cast(User, DummyUser()), cast(Course, DummyCourse()), db)
