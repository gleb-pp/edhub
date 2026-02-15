from unittest.mock import MagicMock, patch

import pytest

from src.exceptions.students import (
    NoAccessToStudentInfoError,
    StudentRoleConflictError,
    StudentRoleRequiredError,
)
from src.policies.students import StudentPolicy
from src.repo.courses import Course
from src.repo.users import User


class TestStudentPolicy:

    def test_assert_student_access_success(self):
        mock_user = MagicMock(spec=User)
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        StudentPolicy.assert_student_access(mock_user, mock_course, mock_db)

    def test_assert_student_access_fail(self):
        mock_user = MagicMock(spec=User)
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = False

        with pytest.raises(StudentRoleRequiredError):
            StudentPolicy.assert_student_access(mock_user, mock_course, mock_db)

    def test_assert_not_student_success(self):
        mock_user = MagicMock(spec=User)
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = False

        StudentPolicy.assert_not_student(mock_user, mock_course, mock_db)

    def test_assert_not_student_conflict(self):
        mock_user = MagicMock(spec=User)
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        with pytest.raises(StudentRoleConflictError):
            StudentPolicy.assert_not_student(mock_user, mock_course, mock_db)

    @patch("src.policies.students.CoursePolicy.assert_course_access")
    @patch("src.policies.students.TeacherPolicy.check_teacher_access")
    @patch("src.policies.students.ParentPolicy.check_parent_of_student")
    def test_access_to_student_denied(
        self, mock_parent_check, mock_teacher_check, mock_course_assert,
    ):
        mock_teacher_check.return_value = False
        mock_parent_check.return_value = False

        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_user = MagicMock(spec=User)
        mock_user.email = "other@test.com"
        mock_user.isadmin = False
        mock_course = MagicMock(spec=Course)
        mock_course.id = 1
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        with pytest.raises(NoAccessToStudentInfoError):
            StudentPolicy.assert_access_to_student(mock_student, mock_user, mock_course, mock_db)

    @patch("src.policies.students.CoursePolicy.assert_course_access")
    @patch("src.policies.students.TeacherPolicy.check_teacher_access")
    @patch("src.policies.students.ParentPolicy.check_parent_of_student")
    def test_access_to_student_as_self(
        self, mock_parent_check, mock_teacher_check, mock_course_assert,
    ):
        mock_teacher_check.return_value = False
        mock_parent_check.return_value = False

        mock_student = MagicMock(spec=User)
        mock_student.email = "same@test.com"
        mock_user = MagicMock(spec=User)
        mock_user.email = "same@test.com"
        mock_user.isadmin = False
        mock_course = MagicMock(spec=Course)
        mock_course.id = 1
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        StudentPolicy.assert_access_to_student(mock_student, mock_user, mock_course, mock_db)

    @patch("src.policies.students.CoursePolicy.assert_course_access")
    @patch("src.policies.students.TeacherPolicy.check_teacher_access")
    @patch("src.policies.students.ParentPolicy.check_parent_of_student")
    def test_access_to_student_as_teacher(
        self, mock_parent_check, mock_teacher_check, mock_course_assert,
    ):
        mock_teacher_check.return_value = True
        mock_parent_check.return_value = False

        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_user = MagicMock(spec=User)
        mock_user.email = "teacher@test.com"
        mock_user.isadmin = False
        mock_course = MagicMock(spec=Course)
        mock_course.id = 1
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        StudentPolicy.assert_access_to_student(mock_student, mock_user, mock_course, mock_db)

    @patch("src.policies.students.CoursePolicy.assert_course_access")
    @patch("src.policies.students.TeacherPolicy.check_teacher_access")
    @patch("src.policies.students.ParentPolicy.check_parent_of_student")
    def test_access_to_student_as_parent(
        self, mock_parent_check, mock_teacher_check, mock_course_assert,
    ):
        mock_teacher_check.return_value = False
        mock_parent_check.return_value = True

        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_user = MagicMock(spec=User)
        mock_user.email = "parent@test.com"
        mock_user.isadmin = False
        mock_course = MagicMock(spec=Course)
        mock_course.id = 1
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        StudentPolicy.assert_access_to_student(mock_student, mock_user, mock_course, mock_db)

    @patch("src.policies.students.CoursePolicy.assert_course_access")
    @patch("src.policies.students.TeacherPolicy.check_teacher_access")
    @patch("src.policies.students.ParentPolicy.check_parent_of_student")
    def test_access_to_student_as_admin(
        self, mock_parent_check, mock_teacher_check, mock_course_assert,
    ):
        mock_teacher_check.return_value = False
        mock_parent_check.return_value = False

        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_user = MagicMock(spec=User)
        mock_user.email = "admin@test.com"
        mock_user.isadmin = True
        mock_course = MagicMock(spec=Course)
        mock_course.id = 1
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        StudentPolicy.assert_access_to_student(mock_student, mock_user, mock_course, mock_db)
