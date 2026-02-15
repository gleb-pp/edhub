import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.users import (
    get_user_info,
    get_my_role,
    create_user,
    login,
    change_password,
    get_my_instructor_courses,
    remove_user
)
from src.exceptions import admins as admin_errors
from src.exceptions import courses as course_errors
from src.exceptions import users as user_errors
from src.models.common import Success


pytestmark = pytest.mark.asyncio


class TestUsersRouter:

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_get_user_info_success(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()
        mock_user.email = "user@test.com"
        mock_user.name = "Test User"

        mock_user_service.get_user.return_value = mock_user

        with patch('src.routers.users.User.model_validate') as mock_validate:
            expected_result = {"email": "user@test.com", "name": "Test User"}
            mock_validate.return_value = expected_result
            result = await get_user_info("user@test.com", mock_db)

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_validate.assert_called_once_with(mock_user)

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_get_user_info_not_found(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_user_info("user@test.com", mock_db)

        assert exc_info.value.status_code == 404

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.CourseService')
    @patch('src.routers.users.get_db')
    @patch('src.routers.users.get_current_user')
    async def test_get_my_role_success(
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
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.users.TeacherPolicy.check_instructor_access', return_value=True),
            patch('src.routers.users.TeacherPolicy.check_teacher_access', return_value=False),
            patch('src.routers.users.StudentPolicy.check_student_access', return_value=False),
            patch('src.routers.users.ParentPolicy.check_parent_access', return_value=False)
        ):
            result = await get_my_role("course-123", mock_db, "user@test.com")

        assert result.is_instructor is True
        assert result.is_teacher is False
        assert result.is_student is False
        assert result.is_parent is False
        assert result.is_admin is False
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    @patch('src.routers.users.get_current_user')
    async def test_get_my_role_user_not_found(
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
            await get_my_role("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.CourseService')
    @patch('src.routers.users.get_db')
    @patch('src.routers.users.get_current_user')
    async def test_get_my_role_course_not_found(
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
            await get_my_role("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_create_user_success(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = mock_user_service.create_user.return_value
        mock_user.email = "user@test.com"

        mock_user_service.get_access_token.return_value = "jwt_token"

        with (
            patch('src.routers.users.UserService.validate_user_email'),
            patch('src.routers.users.UserService.validate_user_name'),
            patch('src.routers.users.UserService.validate_password_length')
        ):
            result = await create_user("user@test.com", "Test User", "Pass123!@#", mock_db)

        assert result.access_token == "jwt_token"
        mock_user_service.validate_user_email.assert_called_once_with("user@test.com")
        mock_user_service.validate_user_name.assert_called_once_with("Test User")
        mock_user_service.validate_password_length.assert_called_once_with("Pass123!@#")
        mock_user_service.create_user.assert_called_once_with("user@test.com", "Test User", "Pass123!@#")
        mock_user_service.get_access_token.assert_called_once_with(mock_user)

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_create_user_validation_error(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.validate_user_email.side_effect = user_errors.EmailFormatError()

        with pytest.raises(HTTPException) as exc_info:
            await create_user("invalid-email", "Test User", "Pass123!@#", mock_db)

        assert exc_info.value.status_code == 422

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_create_user_exists(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_access_token.return_value = "jwt_token"

        mock_user_service.validate_user_email.return_value = None
        mock_user_service.validate_user_name.return_value = None
        mock_user_service.validate_password_length.return_value = None
        mock_user_service.create_user.side_effect = user_errors.UserExistsError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await create_user("user@test.com", "Test User", "Pass123!@#", mock_db)

        assert exc_info.value.status_code == 409

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_login_success(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()
        mock_user.email = "user@test.com"

        mock_user_service.get_user.return_value = mock_user
        mock_user_service.get_access_token.return_value = "jwt_token"

        result = await login("user@test.com", "password", mock_db)

        assert result.access_token == "jwt_token"
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_user_service.verify_password.assert_called_once_with(mock_user, "password")
        mock_user_service.get_access_token.assert_called_once_with(mock_user)

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_login_user_not_found(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await login("user@test.com", "password", mock_db)

        assert exc_info.value.status_code == 401

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_login_invalid_password(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user
        mock_user_service.verify_password.side_effect = user_errors.InvalidPasswordError()

        with pytest.raises(HTTPException) as exc_info:
            await login("user@test.com", "wrong_password", mock_db)

        assert exc_info.value.status_code == 401

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_change_password_success(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()

        mock_user_service.get_user.return_value = mock_user

        result = await change_password("user@test.com", "old_pass", "new_pass123!@#", mock_db)

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_user_service.verify_password.assert_called_once_with(mock_user, "old_pass")
        mock_user_service.validate_password_length.assert_called_once_with("new_pass123!@#")
        mock_user_service.change_password.assert_called_once_with(mock_user, "new_pass123!@#")
        mock_db.commit.assert_called_once()

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_change_password_user_not_found(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await change_password("user@test.com", "old_pass", "new_pass123!@#", mock_db)

        assert exc_info.value.status_code == 401

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    async def test_change_password_weak_new_password(
        self,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user
        mock_user_service.verify_password.return_value = None
        mock_user_service.validate_password_length.side_effect = user_errors.WeakPasswordError()

        with pytest.raises(HTTPException) as exc_info:
            await change_password("user@test.com", "old_pass", "weak", mock_db)

        assert exc_info.value.status_code == 422

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    @patch('src.routers.users.get_current_user')
    async def test_get_my_instructor_courses_success(
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

        mock_user = MagicMock()
        mock_courses = [MagicMock(), MagicMock()]

        mock_user_service.get_user.return_value = mock_user
        mock_user_service.get_instructor_courses.return_value = mock_courses

        with patch('src.routers.users.CourseID.model_validate') as mock_validate:
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_my_instructor_courses(mock_db, "user@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_user_service.get_instructor_courses.assert_called_once_with(mock_user)
        assert mock_validate.call_count == 2

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    @patch('src.routers.users.get_current_user')
    async def test_get_my_instructor_courses_user_not_found(
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
            await get_my_instructor_courses(mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    @patch('src.routers.users.get_current_user')
    async def test_remove_user_success(
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

        mock_user = MagicMock()

        mock_user_service.get_user.return_value = mock_user

        result = await remove_user(mock_db, "user@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_user_service.delete_user.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    @patch('src.routers.users.get_current_user')
    async def test_remove_user_not_found(
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
            await remove_user(mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.users.UserService')
    @patch('src.routers.users.get_db')
    @patch('src.routers.users.get_current_user')
    async def test_remove_user_last_admin(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user
        mock_user_service.delete_user.side_effect = admin_errors.DeleteLastAdminError()

        with pytest.raises(HTTPException) as exc_info:
            await remove_user(mock_db, "admin@test.com")

        assert exc_info.value.status_code == 403
