from unittest.mock import MagicMock, patch

import pytest

from src.exceptions.parents import (
    NoAccessToParentInfoError,
    ParentOfStudentRoleConflictError,
    ParentOfStudentRoleRequiredError,
    ParentRoleConflictError,
    ParentRoleRequiredError,
)
from src.policies import ParentPolicy
from src.repo.courses import Course
from src.repo.users import User


class TestParentPolicy:
    """Tests for the ParentPolicy class."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Fixture for a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_parent(self) -> MagicMock:
        """Fixture for a mock parent user."""
        parent = MagicMock(spec=User)
        parent.email = "parent@test.com"
        parent.is_admin = False
        return parent

    @pytest.fixture
    def mock_student(self) -> MagicMock:
        """Fixture for a mock student user."""
        student = MagicMock(spec=User)
        student.email = "student@test.com"
        return student

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        """Fixture for a mock course."""
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @pytest.mark.parametrize(
        ("method_name", "args", "check_exists" ,"expected_exception"),
        [
            ("assert_parent_access", ["mock_parent", "mock_course"], True, None),
            ("assert_parent_access", ["mock_parent", "mock_course"], False, ParentRoleRequiredError),
            ("assert_not_parent", ["mock_parent", "mock_course"], True, ParentRoleConflictError),
            ("assert_not_parent", ["mock_parent", "mock_course"], False, None),
            ("assert_parent_of_student", ["mock_parent", "mock_student", "mock_course"], True, None),
            ("assert_parent_of_student", ["mock_parent", "mock_student", "mock_course"], False, ParentOfStudentRoleRequiredError),
            ("assert_not_parent_of_student", ["mock_parent", "mock_student", "mock_course"], True, ParentOfStudentRoleConflictError),
            ("assert_not_parent_of_student", ["mock_parent", "mock_student", "mock_course"], False, None),
        ],
        ids=[
            "assert_parent_access_success",
            "assert_parent_access_fail",
            "assert_not_parent_fail",
            "assert_not_parent_success",
            "assert_parent_of_student_success",
            "assert_parent_of_student_fail",
            "assert_not_parent_of_student_fail",
            "assert_not_parent_of_student_success",
        ],
    )
    def test_parent_assertions(
        self,
        request: pytest.FixtureRequest,
        mock_db: MagicMock,
        mock_parent: MagicMock,
        mock_student: MagicMock,
        mock_course: MagicMock,
        method_name: str,
        args: list,
        check_exists: bool,
        expected_exception: type[Exception] | None,
    ) -> None:
        """Test the parent assertion methods with various scenarios."""
        mock_db.query.return_value.scalar.return_value = check_exists
        resolved_args = [request.getfixturevalue(arg) if isinstance(arg, str) else arg for arg in args]
        method = getattr(ParentPolicy, method_name)

        if expected_exception:
            with pytest.raises(expected_exception):
                method(*resolved_args, mock_db)
        else:
            method(*resolved_args, mock_db)

        mock_db.query.assert_called_once()
        mock_db.query.return_value.scalar.assert_called_once()

    @pytest.mark.parametrize(
        ("scenario", "user_email", "is_admin", "teacher_check", "parent_exists", "expected_exception"),
        [
            ("denied_other_user", "other@test.com", False, False, True, NoAccessToParentInfoError),
            ("allowed_same_user", "parent@test.com", False, False, True, None),
            ("allowed_teacher", "teacher@test.com", False, True, True, None),
            ("allowed_admin", "admin@test.com", True, False, True, None),
            ("parent_not_in_course", "parent@test.com", False, False, False, ParentRoleRequiredError),
        ],
        ids=[
            "denied_other_user",
            "allowed_same_user",
            "allowed_teacher",
            "allowed_admin",
            "parent_not_in_course",
        ],
    )
    @patch("src.policies.parents.CoursePolicy.assert_course_access")
    @patch("src.policies.parents.TeacherPolicy.check_teacher_access")
    def test_assert_access_to_parent(
        self,
        mock_teacher_check: MagicMock,
        mock_course_assert: MagicMock,
        mock_db: MagicMock,
        mock_parent: MagicMock,
        mock_course: MagicMock,
        scenario: str,
        user_email: str,
        is_admin: bool,
        teacher_check: bool,
        parent_exists: bool,
        expected_exception: type[Exception] | None,
    ) -> None:
        """Test the assert_access_to_parent method with various scenarios."""
        if scenario == "allowed_same_user":
            mock_user = mock_parent
            mock_user.is_admin = is_admin
        else:
            mock_user = MagicMock(spec=User)
            mock_user.email = user_email
            mock_user.is_admin = is_admin

        mock_teacher_check.return_value = teacher_check
        mock_db.query.return_value.scalar.return_value = parent_exists

        if expected_exception:
            with pytest.raises(expected_exception):
                ParentPolicy.assert_access_to_parent(mock_parent, mock_user, mock_course, mock_db)
        else:
            ParentPolicy.assert_access_to_parent(mock_parent, mock_user, mock_course, mock_db)

        mock_course_assert.assert_called_once_with(mock_user, mock_course, mock_db)
