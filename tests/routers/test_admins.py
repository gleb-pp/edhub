from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import admins as admin_errors
from src.exceptions import users as user_errors
from src.policies import AdminPolicy
from src.routers.admins import (
    get_admins,
    get_all_courses,
    get_all_users,
    give_admin_permissions,
    remove_user,
)

pytestmark = pytest.mark.asyncio


class TestAdminRouter:

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_remove_user_success(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_admin_user = MagicMock()
        mock_deleted_user = MagicMock()

        mock_user_service.get_user.side_effect = [mock_admin_user, mock_deleted_user]

        result = await remove_user("user@test.com", mock_db, "admin@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("admin@test.com")
        mock_user_service.get_user.assert_any_call("user@test.com")
        mock_user_service.delete_user.assert_called_once_with(mock_deleted_user)
        mock_db.commit.assert_called_once()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_remove_user_admin_not_found(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("admin@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await remove_user("user@test.com", mock_db, "admin@test.com")

        assert exc_info.value.status_code == 401
        mock_user_service.delete_user.assert_not_called()
        mock_db.commit.assert_not_called()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_remove_user_deleted_user_not_found(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_admin_user = MagicMock()
        mock_user_service.get_user.side_effect = [mock_admin_user, user_errors.UserNotFoundError("user@test.com")]

        with pytest.raises(HTTPException) as exc_info:
            await remove_user("user@test.com", mock_db, "admin@test.com")

        assert exc_info.value.status_code == 404
        mock_user_service.delete_user.assert_not_called()
        mock_db.commit.assert_not_called()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_remove_user_not_admin(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user

        with (
            patch.object(AdminPolicy, "assert_user_is_admin", side_effect=admin_errors.AdminRoleRequiredError("user@test.com")),
            pytest.raises(HTTPException) as exc_info
        ):
            await remove_user("user@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 403
        mock_db.commit.assert_not_called()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_remove_user_last_admin(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_admin_user = MagicMock()
        mock_deleted_user = MagicMock()

        mock_user_service.get_user.side_effect = [mock_admin_user, mock_deleted_user]
        mock_user_service.delete_user.side_effect = admin_errors.DeleteLastAdminError()

        with pytest.raises(HTTPException) as exc_info:
            await remove_user("admin@test.com", mock_db, "admin@test.com")

        assert exc_info.value.status_code == 403
        mock_db.commit.assert_not_called()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_give_admin_permissions_success(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_admin = MagicMock()
        mock_new_admin = MagicMock()

        mock_user_service.get_user.side_effect = [mock_admin, mock_new_admin]

        result = await give_admin_permissions("new_admin@test.com", mock_db, "admin@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("admin@test.com")
        mock_user_service.get_user.assert_any_call("new_admin@test.com")
        mock_user_service.give_admin_permissions.assert_called_once_with(mock_new_admin)
        mock_db.commit.assert_called_once()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_give_admin_permissions_admin_not_found(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("admin@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await give_admin_permissions("new_admin@test.com", mock_db, "admin@test.com")

        assert exc_info.value.status_code == 401
        mock_user_service.give_admin_permissions.assert_not_called()
        mock_db.commit.assert_not_called()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_give_admin_permissions_new_admin_not_found(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_admin = MagicMock()
        mock_user_service.get_user.side_effect = [mock_admin, user_errors.UserNotFoundError("new_admin@test.com")]

        with pytest.raises(HTTPException) as exc_info:
            await give_admin_permissions("new_admin@test.com", mock_db, "admin@test.com")

        assert exc_info.value.status_code == 404
        mock_user_service.give_admin_permissions.assert_not_called()
        mock_db.commit.assert_not_called()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_give_admin_permissions_not_admin(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user

        with (
            patch.object(AdminPolicy, "assert_user_is_admin", side_effect=admin_errors.AdminRoleRequiredError("user@test.com")),
            pytest.raises(HTTPException) as exc_info
        ):
            await give_admin_permissions("new_admin@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 403
        mock_db.commit.assert_not_called()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_get_all_users_success(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_admin = MagicMock()
        mock_users = [MagicMock(), MagicMock()]

        mock_user_service.get_user.return_value = mock_admin
        mock_user_service.get_all_users.return_value = mock_users

        with patch("src.routers.admins.User.model_validate") as mock_validate:
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_all_users(mock_db, "admin@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("admin@test.com")
        mock_user_service.get_all_users.assert_called_once()
        assert mock_validate.call_count == 2

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_get_all_users_admin_not_found(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("admin@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_all_users(mock_db, "admin@test.com")

        assert exc_info.value.status_code == 401
        mock_user_service.get_all_users.assert_not_called()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_get_all_users_not_admin(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user

        with (
            patch.object(AdminPolicy, "assert_user_is_admin", side_effect=admin_errors.AdminRoleRequiredError("user@test.com")),
            pytest.raises(HTTPException) as exc_info
        ):
            await get_all_users(mock_db, "user@test.com")

        assert exc_info.value.status_code == 403
        mock_user_service.get_all_users.assert_not_called()

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    async def test_get_admins_success(self, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_admins = [MagicMock(), MagicMock()]
        mock_user_service.get_admins.return_value = mock_admins

        with patch("src.routers.admins.User.model_validate") as mock_validate:
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_admins(mock_db)

        assert len(result) == 2
        mock_user_service.get_admins.assert_called_once()
        assert mock_validate.call_count == 2

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.CourseService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_get_all_courses_success(self, mock_get_current_user, mock_get_db, mock_course_service_class, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_admin = MagicMock()
        mock_courses = [MagicMock(), MagicMock()]

        mock_user_service.get_user.return_value = mock_admin
        mock_course_service.get_all_courses.return_value = mock_courses

        with patch("src.routers.admins.Course.model_validate") as mock_validate:
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_all_courses(mock_db, "admin@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("admin@test.com")
        mock_course_service.get_all_courses.assert_called_once()
        assert mock_validate.call_count == 2

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_get_all_courses_admin_not_found(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("admin@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_all_courses(mock_db, "admin@test.com")

        assert exc_info.value.status_code == 401

    @patch("src.routers.admins.UserService")
    @patch("src.routers.admins.get_db")
    @patch("src.routers.admins.get_current_user")
    async def test_get_all_courses_not_admin(self, mock_get_current_user, mock_get_db, mock_user_service_class):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user

        with (
            patch.object(AdminPolicy, "assert_user_is_admin", side_effect=admin_errors.AdminRoleRequiredError("user@test.com")),
            pytest.raises(HTTPException) as exc_info
        ):
            await get_all_courses(mock_db, "user@test.com")

        assert exc_info.value.status_code == 403
