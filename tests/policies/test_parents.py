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

    def test_assert_parent_access_success(self):
        mock_user = MagicMock(spec=User)
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True
        
        ParentPolicy.assert_parent_access(mock_user, mock_course, mock_db)

    def test_assert_parent_access_fail(self):
        mock_user = MagicMock(spec=User)
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = False

        with pytest.raises(ParentRoleRequiredError):
            ParentPolicy.assert_parent_access(mock_user, mock_course, mock_db)

    def test_assert_not_parent_fail(self):
        mock_user = MagicMock(spec=User)
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        with pytest.raises(ParentRoleConflictError):
            ParentPolicy.assert_not_parent(mock_user, mock_course, mock_db)

    def test_assert_parent_of_student_required(self):
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_student = MagicMock(spec=User)
        mock_student.email = "s@test.com"
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = False

        with pytest.raises(ParentOfStudentRoleRequiredError):
            ParentPolicy.assert_parent_of_student(mock_parent, mock_student, mock_course, mock_db)

    def test_assert_not_parent_of_student(self):
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_student = MagicMock(spec=User)
        mock_student.email = "s@test.com"
        mock_course = MagicMock(spec=Course)
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        with pytest.raises(ParentOfStudentRoleConflictError):
            ParentPolicy.assert_not_parent_of_student(mock_parent, mock_student, mock_course, mock_db)

    @patch("src.policies.parents.CoursePolicy.assert_course_access")
    @patch("src.policies.parents.TeacherPolicy.check_teacher_access")
    def test_assert_access_to_parent_denied(self, mock_teacher_check, mock_course_assert):
        mock_teacher_check.return_value = False
        
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_user = MagicMock(spec=User)
        mock_user.email = "other@test.com"
        mock_user.isadmin = False
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        with pytest.raises(NoAccessToParentInfoError):
            ParentPolicy.assert_access_to_parent(mock_parent, mock_user, mock_course, mock_db)

    @patch("src.policies.parents.CoursePolicy.assert_course_access")
    @patch("src.policies.parents.TeacherPolicy.check_teacher_access")
    def test_assert_access_to_parent_as_same_user(self, mock_teacher_check, mock_course_assert):
        mock_teacher_check.return_value = False
        
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "same@test.com"
        mock_user = MagicMock(spec=User)
        mock_user.email = "same@test.com"
        mock_user.isadmin = False
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        ParentPolicy.assert_access_to_parent(mock_parent, mock_user, mock_course, mock_db)

    @patch("src.policies.parents.CoursePolicy.assert_course_access")
    @patch("src.policies.parents.TeacherPolicy.check_teacher_access")
    def test_assert_access_to_parent_as_admin(self, mock_teacher_check, mock_course_assert):
        mock_teacher_check.return_value = False
        
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_user = MagicMock(spec=User)
        mock_user.email = "admin@test.com"
        mock_user.isadmin = True
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        ParentPolicy.assert_access_to_parent(mock_parent, mock_user, mock_course, mock_db)
