import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.teachers import (
    get_course_teachers,
    invite_teacher,
    remove_teacher,
    change_course_instructor
)
from src.exceptions import courses as course_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success


pytestmark = pytest.mark.asyncio


class TestTeachersRouter:

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.TeacherService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_get_course_teachers_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_teacher_service_class,
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
        mock_teacher_service = MagicMock()
        mock_teacher_service_class.return_value = mock_teacher_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()
        mock_teachers = [MagicMock(), MagicMock()]

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_teacher_service.get_course_teachers.return_value = mock_teachers

        with (
            patch('src.routers.teachers.CoursePolicy.assert_course_access') as mock_assert_access,
            patch('src.routers.teachers.User.model_validate') as mock_validate
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_course_teachers("course-123", mock_db, "student@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_teacher_service.get_course_teachers.assert_called_once_with(mock_course)
        assert mock_validate.call_count == 2

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_get_course_teachers_user_not_found(
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
            await get_course_teachers("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_get_course_teachers_course_not_found(
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
            await get_course_teachers("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_get_course_teachers_participant_role_required(
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
            patch('src.routers.teachers.CoursePolicy.assert_course_access') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = course_errors.ParticipantRoleRequiredError("non-participant@test.com", "course-123")
            await get_course_teachers("course-123", mock_db, "non-participant@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.TeacherService')
    @patch('src.routers.teachers.PersonalizationService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_invite_teacher_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_teacher_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_teacher_service = MagicMock()
        mock_teacher_service_class.return_value = mock_teacher_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_instructor = MagicMock()
        mock_instructor.isadmin = False
        mock_course = MagicMock()
        mock_new_teacher = MagicMock()

        mock_user_service.get_user.side_effect = [mock_instructor, mock_new_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access') as mock_assert_instructor,
            patch('src.routers.teachers.TeacherPolicy.assert_not_teacher') as mock_assert_not_teacher,
            patch('src.routers.teachers.StudentPolicy.assert_not_student') as mock_assert_not_student,
            patch('src.routers.teachers.ParentPolicy.assert_not_parent') as mock_assert_not_parent
        ):
            result = await invite_teacher("course-123", "new_teacher@test.com", mock_db, "instructor@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("instructor@test.com")
        mock_user_service.get_user.assert_any_call("new_teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_instructor.assert_called_once_with(mock_instructor, mock_course, mock_db)
        mock_assert_not_teacher.assert_called_once_with(mock_new_teacher, mock_course, mock_db)
        mock_assert_not_student.assert_called_once_with(mock_new_teacher, mock_course, mock_db)
        mock_assert_not_parent.assert_called_once_with(mock_new_teacher, mock_course, mock_db)
        mock_teacher_service.invite_teacher.assert_called_once_with(mock_new_teacher, mock_course)
        mock_personalization_service.add_course_participant.assert_called_once_with(mock_course, mock_new_teacher)
        mock_db.commit.assert_called_once()

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_invite_teacher_instructor_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("instructor@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await invite_teacher("course-123", "new_teacher@test.com", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_invite_teacher_new_teacher_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_instructor = MagicMock()
        mock_user_service.get_user.side_effect = [mock_instructor, user_errors.UserNotFoundError("new_teacher@test.com")]

        with pytest.raises(HTTPException) as exc_info:
            await invite_teacher("course-123", "new_teacher@test.com", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 404

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_invite_teacher_instructor_role_required(
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

        mock_instructor = MagicMock()
        mock_instructor.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_instructor
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access') as mock_assert_instructor,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_instructor.side_effect = teacher_errors.InstructorRoleRequiredError("teacher@test.com", "course-123")
            await invite_teacher("course-123", "new_teacher@test.com", mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_invite_teacher_conflict(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_instructor = MagicMock()
        mock_instructor.isadmin = False
        mock_new_teacher = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_instructor, mock_new_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access'),
            patch('src.routers.teachers.TeacherPolicy.assert_not_teacher') as mock_assert_not_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_not_teacher.side_effect = teacher_errors.TeacherRoleConflictError("new_teacher@test.com", "course-123")
            await invite_teacher("course-123", "new_teacher@test.com", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 409

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.TeacherService')
    @patch('src.routers.teachers.PersonalizationService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_remove_teacher_success_as_instructor(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_teacher_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_teacher_service = MagicMock()
        mock_teacher_service_class.return_value = mock_teacher_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_instructor = MagicMock()
        mock_instructor.isadmin = False
        mock_course = MagicMock()
        mock_teacher = MagicMock()

        mock_user_service.get_user.side_effect = [mock_instructor, mock_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access') as mock_assert_instructor,
            patch('src.routers.teachers.TeacherPolicy.assert_teacher_access') as mock_assert_teacher
        ):
            result = await remove_teacher("course-123", "teacher@test.com", mock_db, "instructor@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("instructor@test.com")
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_instructor.assert_called_once_with(mock_instructor, mock_course, mock_db)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_teacher_service.remove_teacher.assert_called_once_with(mock_teacher, mock_course)
        mock_personalization_service.remove_course_participant.assert_called_once_with(mock_course, mock_teacher)
        mock_db.commit.assert_called_once()

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.TeacherService')
    @patch('src.routers.teachers.PersonalizationService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_remove_teacher_success_as_admin(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_teacher_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_teacher_service = MagicMock()
        mock_teacher_service_class.return_value = mock_teacher_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_admin = MagicMock()
        mock_admin.isadmin = True
        mock_course = MagicMock()
        mock_course.instructor = "instructor@test.com"
        mock_instructor = MagicMock()
        mock_teacher = MagicMock()

        mock_user_service.get_user.side_effect = [mock_admin, mock_instructor, mock_teacher]
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.teachers.TeacherPolicy.assert_teacher_access') as mock_assert_teacher:
            result = await remove_teacher("course-123", "teacher@test.com", mock_db, "admin@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("admin@test.com")
        mock_user_service.get_user.assert_any_call("instructor@test.com")
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_teacher_service.remove_teacher.assert_called_once_with(mock_teacher, mock_course)
        mock_personalization_service.remove_course_participant.assert_called_once_with(mock_course, mock_teacher)
        mock_db.commit.assert_called_once()

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_remove_teacher_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("instructor@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await remove_teacher("course-123", "teacher@test.com", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_remove_teacher_teacher_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_instructor = MagicMock()
        mock_instructor.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_instructor, user_errors.UserNotFoundError("teacher@test.com")]
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.teachers.TeacherPolicy.assert_instructor_access'):
            with pytest.raises(HTTPException) as exc_info:
                await remove_teacher("course-123", "teacher@test.com", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_remove_teacher_instructor_role_required(
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

        mock_instructor = MagicMock()
        mock_instructor.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_instructor
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access') as mock_assert_instructor,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_instructor.side_effect = teacher_errors.InstructorRoleRequiredError("teacher@test.com", "course-123")
            await remove_teacher("course-123", "teacher@test.com", mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_remove_teacher_teacher_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_instructor = MagicMock()
        mock_instructor.isadmin = False
        mock_not_teacher = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_instructor, mock_not_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access'),
            patch('src.routers.teachers.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("not_teacher@test.com", "course-123")
            await remove_teacher("course-123", "not_teacher@test.com", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 422

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.TeacherService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_change_course_instructor_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_teacher_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_teacher_service = MagicMock()
        mock_teacher_service_class.return_value = mock_teacher_service

        mock_instructor = MagicMock()
        mock_teacher = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_instructor, mock_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access') as mock_assert_instructor,
            patch('src.routers.teachers.TeacherPolicy.assert_teacher_access') as mock_assert_teacher
        ):
            result = await change_course_instructor("course-123", "new_instructor@test.com", mock_db, "instructor@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("instructor@test.com")
        mock_user_service.get_user.assert_any_call("new_instructor@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_instructor.assert_called_once_with(mock_instructor, mock_course, mock_db)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_teacher_service.change_course_instructor.assert_called_once_with(mock_instructor, mock_teacher, mock_course)
        mock_db.commit.assert_called_once()

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_change_course_instructor_instructor_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("instructor@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await change_course_instructor("course-123", "new_instructor@test.com", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_change_course_instructor_new_instructor_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_instructor = MagicMock()
        mock_course = MagicMock()
        
        mock_user_service.get_user.side_effect = [mock_instructor, user_errors.UserNotFoundError("new_instructor@test.com")]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access'),
            pytest.raises(HTTPException) as exc_info
        ):
            await change_course_instructor("course-123", "new_instructor@test.com", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 404

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_change_course_instructor_instructor_role_required(
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

        mock_instructor = MagicMock()
        mock_instructor.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_instructor
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access') as mock_assert_instructor,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_instructor.side_effect = teacher_errors.InstructorRoleRequiredError("teacher@test.com", "course-123")
            await change_course_instructor("course-123", "new_instructor@test.com", mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.teachers.UserService')
    @patch('src.routers.teachers.CourseService')
    @patch('src.routers.teachers.get_db')
    @patch('src.routers.teachers.get_current_user')
    async def test_change_course_instructor_teacher_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_instructor = MagicMock()
        mock_not_teacher = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_instructor, mock_not_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.teachers.TeacherPolicy.assert_instructor_access'),
            patch('src.routers.teachers.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("not_teacher@test.com", "course-123")
            await change_course_instructor("course-123", "not_teacher@test.com", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 422
