from unittest.mock import MagicMock

import pytest

from src.exceptions.teachers import (
    InstructorRoleRequiredError,
    TeacherRoleConflictError,
    TeacherRoleRequiredError,
)
from src.policies import TeacherPolicy
from src.repo.courses import Course
from src.repo.users import User


class TestTeacherPolicy:
    @pytest.fixture
    def mock_db(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_instructor(self) -> MagicMock:
        user = MagicMock(spec=User)
        user.email = "instructor@test.com"
        return user

    @pytest.fixture
    def mock_teacher(self) -> MagicMock:
        user = MagicMock(spec=User)
        user.email = "teacher@test.com"
        return user

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        user = MagicMock(spec=User)
        user.email = "user@test.com"
        return user

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        course = MagicMock(spec=Course)
        course.instructor = "instructor@test.com"
        course.course_id = 1
        course.title = "Test Course"
        return course

    @pytest.mark.parametrize(
        "user_fixture,expected_exception",
        [
            ("mock_instructor", None),
            ("mock_teacher", InstructorRoleRequiredError),
            ("mock_user", InstructorRoleRequiredError),
        ],
        ids=[
            "assert_instructor_success",
            "assert_instructor_fail_teacher",
            "assert_instructor_fail_user",
        ],
    )
    def test_assert_instructor_access(
        self,
        request,
        mock_course,
        user_fixture,
        expected_exception,
    ) -> None:
        user = request.getfixturevalue(user_fixture)

        if expected_exception:
            with pytest.raises(expected_exception):
                TeacherPolicy.assert_instructor_access(user, mock_course)
        else:
            TeacherPolicy.assert_instructor_access(user, mock_course)

    @pytest.mark.parametrize(
        "method_name,user_fixture,teacher_exists,expected_exception",
        [
            ("assert_teacher_access", "mock_instructor", None, None),
            ("assert_teacher_access", "mock_teacher", True, None),
            ("assert_teacher_access", "mock_teacher", False, TeacherRoleRequiredError),
            ("assert_teacher_access", "mock_user", False, TeacherRoleRequiredError),
            ("assert_not_teacher", "mock_user", False, None),
            ("assert_not_teacher", "mock_instructor", None, TeacherRoleConflictError),
            ("assert_not_teacher", "mock_teacher", True, TeacherRoleConflictError),
            ("assert_not_teacher", "mock_teacher", False, None),
        ],
        ids=[
            "assert_teacher_success_instructor",
            "assert_teacher_success_teacher",
            "assert_teacher_fail_teacher_not_found",
            "assert_teacher_fail_user",
            "assert_not_teacher_success_user",
            "assert_not_teacher_conflict_instructor",
            "assert_not_teacher_conflict_teacher",
            "assert_not_teacher_success_teacher_not_found",
        ],
    )
    def test_teacher_assertions_with_db(
        self,
        request,
        mock_db,
        mock_course,
        method_name,
        user_fixture,
        teacher_exists,
        expected_exception,
    ) -> None:
        user = request.getfixturevalue(user_fixture)
        if teacher_exists is not None:
            mock_db.query.return_value.scalar.return_value = teacher_exists

        method = getattr(TeacherPolicy, method_name)

        if expected_exception:
            with pytest.raises(expected_exception):
                method(user, mock_course, mock_db)
        else:
            method(user, mock_course, mock_db)

        if teacher_exists is not None:
            mock_db.query.assert_called_once()
            mock_db.query.return_value.scalar.assert_called_once()

    @pytest.mark.parametrize(
        "user_fixture,teacher_exists,expected_result",
        [
            ("mock_instructor", None, True),
            ("mock_teacher", True, True),
            ("mock_teacher", False, False),
            ("mock_user", False, False),
        ],
        ids=[
            "instructor_true",
            "teacher_exists_true",
            "teacher_not_found_false",
            "user_false",
        ],
    )
    def test_check_teacher_access(
        self,
        request,
        mock_db,
        mock_course,
        user_fixture,
        teacher_exists,
        expected_result,
    ) -> None:
        user = request.getfixturevalue(user_fixture)
        if teacher_exists is not None:
            mock_db.query.return_value.scalar.return_value = teacher_exists

        result = TeacherPolicy.check_teacher_access(user, mock_course, mock_db)

        assert result is expected_result

        if teacher_exists is not None and user_fixture != "mock_instructor":
            mock_db.query.assert_called_once()
            mock_db.query.return_value.scalar.assert_called_once()
