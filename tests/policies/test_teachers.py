from unittest.mock import MagicMock

import pytest

from src.exceptions.teachers import (
    InstructorRoleRequiredError,
    TeacherRoleConflictError,
    TeacherRoleRequiredError,
)
from src.policies.teachers import TeacherPolicy
from src.repo.courses import Course
from src.repo.users import User


class TestTeacherPolicy:

    def test_assert_instructor_access_success(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "instructor@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_db = MagicMock()
        
        TeacherPolicy.assert_instructor_access(mock_user, mock_course, mock_db)

    def test_assert_instructor_access_fail(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_course.title = "Course Title"
        mock_db = MagicMock()

        with pytest.raises(InstructorRoleRequiredError):
            TeacherPolicy.assert_instructor_access(mock_user, mock_course, mock_db)

    def test_assert_teacher_access_success_as_instructor(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "instructor@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_db = MagicMock()
        
        TeacherPolicy.assert_teacher_access(mock_user, mock_course, mock_db)

    def test_assert_teacher_access_success_as_teacher(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "teacher@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True
        
        TeacherPolicy.assert_teacher_access(mock_user, mock_course, mock_db)

    def test_assert_teacher_access_fail(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_course.title = "Course Title"
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = False

        with pytest.raises(TeacherRoleRequiredError):
            TeacherPolicy.assert_teacher_access(mock_user, mock_course, mock_db)

    def test_assert_not_teacher_success(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = False
        
        TeacherPolicy.assert_not_teacher(mock_user, mock_course, mock_db)

    def test_assert_not_teacher_conflict_as_instructor(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "instructor@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_course.course_id = 1
        mock_db = MagicMock()

        with pytest.raises(TeacherRoleConflictError):
            TeacherPolicy.assert_not_teacher(mock_user, mock_course, mock_db)

    def test_assert_not_teacher_conflict_as_teacher(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "teacher@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_course.course_id = 1
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True

        with pytest.raises(TeacherRoleConflictError):
            TeacherPolicy.assert_not_teacher(mock_user, mock_course, mock_db)

    def test_check_teacher_access_instructor_true(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "instructor@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_db = MagicMock()
        
        result = TeacherPolicy.check_teacher_access(mock_user, mock_course, mock_db)
        assert result is True

    def test_check_teacher_access_teacher_true(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "teacher@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = True
        
        result = TeacherPolicy.check_teacher_access(mock_user, mock_course, mock_db)
        assert result is True

    def test_check_teacher_access_false(self):
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.instructor = "instructor@test.com"
        mock_db = MagicMock()
        mock_db.query().scalar.return_value = False
        
        result = TeacherPolicy.check_teacher_access(mock_user, mock_course, mock_db)
        assert result is False
