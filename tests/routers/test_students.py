import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.students import (
    get_enrolled_students,
    invite_student,
    remove_student
)
from src.exceptions import courses as course_errors
from src.exceptions import students as student_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success


pytestmark = pytest.mark.asyncio


class TestStudentsRouter:

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.StudentService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_get_enrolled_students_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_student_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_student_service = MagicMock()
        mock_student_service_class.return_value = mock_student_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()
        mock_students = [MagicMock(), MagicMock()]

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_student_service.get_enrolled_students.return_value = mock_students

        with (
            patch('src.routers.students.CoursePolicy.assert_course_access') as mock_assert_access,
            patch('src.routers.students.User.model_validate') as mock_validate
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_enrolled_students("course-123", mock_db, "teacher@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_student_service.get_enrolled_students.assert_called_once_with(mock_course)
        assert mock_validate.call_count == 2

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_get_enrolled_students_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_enrolled_students("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_get_enrolled_students_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await get_enrolled_students("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_get_enrolled_students_participant_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "non-participant@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.students.CoursePolicy.assert_course_access') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = course_errors.ParticipantRoleRequiredError("non-participant@test.com", "course-123")
            await get_enrolled_students("course-123", mock_db, "non-participant@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.StudentService')
    @patch('src.routers.students.PersonalizationService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_invite_student_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_student_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_student_service = MagicMock()
        mock_student_service_class.return_value = mock_student_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_student = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.students.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            patch('src.routers.students.StudentPolicy.assert_not_student') as mock_assert_not_student,
            patch('src.routers.students.TeacherPolicy.assert_not_teacher') as mock_assert_not_teacher,
            patch('src.routers.students.ParentPolicy.assert_not_parent') as mock_assert_not_parent
        ):
            result = await invite_student("course-123", "student@test.com", mock_db, "teacher@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_not_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assert_not_teacher.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assert_not_parent.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_student_service.invite_student.assert_called_once_with(mock_student, mock_course)
        mock_personalization_service.add_course_participant.assert_called_once_with(mock_course, mock_student)
        mock_db.commit.assert_called_once()

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_invite_student_teacher_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("teacher@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await invite_student("course-123", "student@test.com", mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_invite_student_student_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_teacher = MagicMock()
        mock_user_service.get_user.side_effect = [mock_teacher, user_errors.UserNotFoundError("student@test.com")]

        with pytest.raises(HTTPException) as exc_info:
            await invite_student("course-123", "student@test.com", mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 404

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_invite_student_teacher_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.students.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123")
            await invite_student("course-123", "student@test.com", mock_db, "student@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_invite_student_conflict(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_student = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.students.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.students.StudentPolicy.assert_not_student') as mock_assert_not_student,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_not_student.side_effect = student_errors.StudentRoleConflictError("student@test.com", "course-123")
            await invite_student("course-123", "student@test.com", mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 409

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.StudentService')
    @patch('src.routers.students.PersonalizationService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_remove_student_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_student_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_student_service = MagicMock()
        mock_student_service_class.return_value = mock_student_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_student = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.students.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            patch('src.routers.students.StudentPolicy.assert_student_access') as mock_assert_student
        ):
            result = await remove_student("course-123", "student@test.com", mock_db, "teacher@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_student_service.remove_student.assert_called_once_with(mock_student, mock_course)
        mock_personalization_service.remove_course_participant.assert_called_once_with(mock_course, mock_student)
        mock_db.commit.assert_called_once()

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_remove_student_teacher_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("teacher@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await remove_student("course-123", "student@test.com", mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_remove_student_student_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_teacher = MagicMock()
        mock_user_service.get_user.side_effect = [mock_teacher, user_errors.UserNotFoundError("student@test.com")]

        with pytest.raises(HTTPException) as exc_info:
            await remove_student("course-123", "student@test.com", mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 404

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_remove_student_teacher_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.students.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123")
            await remove_student("course-123", "student@test.com", mock_db, "student@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.students.UserService')
    @patch('src.routers.students.CourseService')
    @patch('src.routers.students.get_db')
    @patch('src.routers.students.get_current_user')
    async def test_remove_student_student_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_student = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.students.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.students.StudentPolicy.assert_student_access') as mock_assert_student,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_student.side_effect = student_errors.StudentRoleRequiredError("student@test.com", "course-123")
            await remove_student("course-123", "student@test.com", mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 422
