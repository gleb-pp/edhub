from unittest.mock import MagicMock, patch

import pytest

from src.exceptions.students import (
    NoAccessToStudentInfoError,
    StudentRoleConflictError,
    StudentRoleRequiredError,
)
from src.policies import StudentPolicy
from src.repo.courses import Course
from src.repo.users import User


class TestStudentPolicy:
    @pytest.fixture
    def mock_db(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        user = MagicMock(spec=User)
        user.email = "user@test.com"
        user.isadmin = False
        return user

    @pytest.fixture
    def mock_student(self) -> MagicMock:
        student = MagicMock(spec=User)
        student.email = "student@test.com"
        return student

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        course = MagicMock(spec=Course)
        course.course_id = 1
        course.id = 1
        course.title = "Test Course"
        return course

    @pytest.mark.parametrize(
        "method_name,check_exists,expected_exception",
        [
            ("assert_student_access", True, None),
            ("assert_student_access", False, StudentRoleRequiredError),
            ("assert_not_student", False, None),
            ("assert_not_student", True, StudentRoleConflictError),
        ],
        ids=[
            "assert_student_access_success",
            "assert_student_access_fail",
            "assert_not_student_success",
            "assert_not_student_conflict",
        ],
    )
    def test_student_assertions(
        self,
        mock_db,
        mock_user,
        mock_course,
        method_name,
        check_exists,
        expected_exception,
    ) -> None:
        mock_db.query.return_value.scalar.return_value = check_exists
        method = getattr(StudentPolicy, method_name)

        if expected_exception:
            with pytest.raises(expected_exception):
                method(mock_user, mock_course, mock_db)
        else:
            method(mock_user, mock_course, mock_db)

        mock_db.query.assert_called_once()
        mock_db.query.return_value.scalar.assert_called_once()

    @pytest.mark.parametrize(
        "scenario,user_email,is_admin,teacher_check,parent_check,student_exists,expected_exception",
        [
            ("denied_other_user", "other@test.com", False, False, False, True, NoAccessToStudentInfoError),
            ("allowed_self", "student@test.com", False, False, False, True, None),
            ("allowed_teacher", "teacher@test.com", False, True, False, True, None),
            ("allowed_parent", "parent@test.com", False, False, True, True, None),
            ("allowed_admin", "admin@test.com", True, False, False, True, None),
            ("student_not_in_course", "student@test.com", False, False, False, False, StudentRoleRequiredError),
        ],
        ids=[
            "denied_other_user",
            "allowed_self",
            "allowed_teacher",
            "allowed_parent",
            "allowed_admin",
            "student_not_in_course",
        ],
    )
    @patch("src.policies.students.CoursePolicy.assert_course_access")
    @patch("src.policies.students.TeacherPolicy.check_teacher_access")
    @patch("src.policies.students.ParentPolicy.check_parent_of_student")
    def test_assert_access_to_student(
        self,
        mock_parent_check,
        mock_teacher_check,
        mock_course_assert,
        mock_db,
        mock_student,
        mock_course,
        scenario,
        user_email,
        is_admin,
        teacher_check,
        parent_check,
        student_exists,
        expected_exception,
    ) -> None:
        if scenario == "allowed_self":
            mock_user = mock_student
            mock_user.isadmin = is_admin
        else:
            mock_user = MagicMock(spec=User)
            mock_user.email = user_email
            mock_user.isadmin = is_admin

        mock_teacher_check.return_value = teacher_check
        mock_parent_check.return_value = parent_check
        mock_db.query.return_value.scalar.return_value = student_exists

        if expected_exception:
            with pytest.raises(expected_exception):
                StudentPolicy.assert_access_to_student(mock_student, mock_user, mock_course, mock_db)
        else:
            StudentPolicy.assert_access_to_student(mock_student, mock_user, mock_course, mock_db)

        mock_course_assert.assert_called_once_with(mock_user, mock_course, mock_db)
