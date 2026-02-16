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

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_user_service():
    with patch("src.routers.admins.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_get_current_user():
    with patch("src.routers.admins.get_current_user") as mock_func:
        yield mock_func


class TestAdminRouter:

    async def test_remove_user_success(self, mock_db, mock_user_service, mock_get_current_user) -> None:
        mock_get_current_user.return_value = "admin@test.com"
        mock_admin = MagicMock()
        mock_deleted_user = MagicMock()
        mock_user_service.get_user.side_effect = [mock_admin, mock_deleted_user]

        result = await remove_user("user@test.com", mock_db, "admin@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("admin@test.com")
        mock_user_service.get_user.assert_any_call("user@test.com")
        mock_user_service.delete_user.assert_called_once_with(mock_deleted_user)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "current_user,target_user,side_effect,expected_status",
        [
            ("admin@test.com", "user@test.com", user_errors.UserNotFoundError("admin@test.com"), 401),
            ("admin@test.com", "user@test.com", [MagicMock(), user_errors.UserNotFoundError("user@test.com")], 404),
            ("non_admin@test.com", "target@test.com", admin_errors.AdminRoleRequiredError("non_admin@test.com"), 403),
            ("admin@test.com", "admin@test.com", admin_errors.DeleteLastAdminError(), 403),
        ],
    )
    async def test_remove_user_errors(self, mock_db, mock_user_service, mock_get_current_user, current_user, target_user, side_effect, expected_status) -> None:
        mock_get_current_user.return_value = current_user

        if isinstance(side_effect, list):
            mock_user_service.get_user.side_effect = side_effect
            with pytest.raises(HTTPException) as exc:
                await remove_user(target_user, mock_db, current_user)
            assert exc.value.status_code == expected_status
            mock_user_service.delete_user.assert_not_called()

        elif isinstance(side_effect, admin_errors.DeleteLastAdminError):
            mock_admin_user = MagicMock()
            mock_deleted_user = MagicMock()
            mock_user_service.get_user.side_effect = [mock_admin_user, mock_deleted_user]
            mock_user_service.delete_user.side_effect = side_effect

            with pytest.raises(HTTPException) as exc:
                await remove_user(target_user, mock_db, current_user)

            assert exc.value.status_code == expected_status
            mock_user_service.delete_user.assert_called_once_with(mock_deleted_user)
            mock_db.commit.assert_not_called()
            mock_user_service.delete_user.assert_called_once()
            return

        elif isinstance(side_effect, admin_errors.AdminRoleRequiredError):
            mock_user_service.get_user.side_effect = [MagicMock(), MagicMock()]
            with patch.object(AdminPolicy, "assert_user_is_admin", side_effect=side_effect):
                with pytest.raises(HTTPException) as exc:
                    await remove_user(target_user, mock_db, current_user)
                assert exc.value.status_code == expected_status
                mock_user_service.delete_user.assert_not_called()

        else:
            mock_user_service.get_user.side_effect = side_effect
            with pytest.raises(HTTPException) as exc:
                await remove_user(target_user, mock_db, current_user)
            assert exc.value.status_code == expected_status
            mock_user_service.delete_user.assert_not_called()

        mock_db.commit.assert_not_called()

    async def test_give_admin_permissions_success(self, mock_db, mock_user_service, mock_get_current_user) -> None:
        mock_get_current_user.return_value = "admin@test.com"
        mock_admin = MagicMock()
        mock_new_admin = MagicMock()
        mock_user_service.get_user.side_effect = [mock_admin, mock_new_admin]

        result = await give_admin_permissions("new_admin@test.com", mock_db, "admin@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_any_call("admin@test.com")
        mock_user_service.get_user.assert_any_call("new_admin@test.com")
        mock_user_service.give_admin_permissions.assert_called_once_with(mock_new_admin)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "current_user,target_user,side_effect,expected_status",
        [
            ("admin@test.com", "new_admin@test.com", user_errors.UserNotFoundError("admin@test.com"), 401),
            ("admin@test.com", "new_admin@test.com", [MagicMock(), user_errors.UserNotFoundError("new_admin@test.com")], 404),
            ("non_admin@test.com", "new_admin@test.com", admin_errors.AdminRoleRequiredError("non_admin@test.com"), 403),
        ],
    )
    async def test_give_admin_permissions_errors(self, mock_db, mock_user_service, mock_get_current_user, current_user, target_user, side_effect, expected_status) -> None:
        mock_get_current_user.return_value = current_user

        if isinstance(side_effect, list):
            mock_user_service.get_user.side_effect = side_effect
        elif isinstance(side_effect, admin_errors.AdminRoleRequiredError):
            mock_user_service.get_user.side_effect = [MagicMock(), MagicMock()]
        else:
            mock_user_service.get_user.side_effect = side_effect

        if isinstance(side_effect, admin_errors.AdminRoleRequiredError):
            with patch.object(AdminPolicy, "assert_user_is_admin", side_effect=side_effect):
                with pytest.raises(HTTPException) as exc:
                    await give_admin_permissions(target_user, mock_db, current_user)
        else:
            with pytest.raises(HTTPException) as exc:
                await give_admin_permissions(target_user, mock_db, current_user)

        assert exc.value.status_code == expected_status
        mock_user_service.give_admin_permissions.assert_not_called()
        mock_db.commit.assert_not_called()

    async def test_get_all_users_success(self, mock_db, mock_user_service) -> None:
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

    async def test_get_admins_success(self, mock_db, mock_user_service) -> None:
        mock_admins = [MagicMock(), MagicMock()]
        mock_user_service.get_admins.return_value = mock_admins

        with patch("src.routers.admins.User.model_validate") as mock_validate:
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_admins(mock_db)

        assert len(result) == 2
        mock_user_service.get_admins.assert_called_once()
        assert mock_validate.call_count == 2

    async def test_get_all_courses_success(self, mock_db, mock_user_service) -> None:
        with patch("src.routers.admins.CourseService") as mock_course_service_class:
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
