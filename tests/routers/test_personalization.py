import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.personalization import (
    get_course_emoji,
    change_courses_order,
    set_course_emoji
)
from src.exceptions import courses as course_errors
from src.exceptions import personalization as personalization_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.settings.course import course_settings


pytestmark = pytest.mark.asyncio


class TestPersonalizationRouter:

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.CourseService')
    @patch('src.routers.personalization.PersonalizationService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_get_course_emoji_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
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
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_user = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_personalization_service.get_course_emoji.return_value = 5

        with patch('src.routers.personalization.CoursePolicy.assert_course_access') as mock_assert_access:
            result = await get_course_emoji(mock_db, "course-123", "user@test.com")

        assert result.emoji_id == 5
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_personalization_service.get_course_emoji.assert_called_once_with(mock_course, mock_user)

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_get_course_emoji_user_not_found(
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
            await get_course_emoji(mock_db, "course-123", "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.CourseService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_get_course_emoji_course_not_found(
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
            await get_course_emoji(mock_db, "course-123", "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.CourseService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_get_course_emoji_participant_role_required(
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
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.personalization.CoursePolicy.assert_course_access') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = course_errors.ParticipantRoleRequiredError("user@test.com", "course-123")
            await get_course_emoji(mock_db, "course-123", "user@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.PersonalizationService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_change_courses_order_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user

        new_order = ["course-1", "course-2", "course-3"]
        result = await change_courses_order(mock_db, new_order, "user@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_personalization_service.change_courses_order.assert_called_once_with(mock_user, new_order)
        mock_db.commit.assert_called_once()

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_change_courses_order_user_not_found(
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
            await change_courses_order(mock_db, ["course-1"], "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.PersonalizationService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_change_courses_order_incorrect_order(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user

        with (
            pytest.raises(HTTPException) as exc_info
        ):
            mock_personalization_service.change_courses_order.side_effect = personalization_errors.IncorrectCoursesOrderError()
            await change_courses_order(mock_db, ["wrong-order"], "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.CourseService')
    @patch('src.routers.personalization.PersonalizationService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_set_course_emoji_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
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
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_user = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.personalization.CoursePolicy.assert_course_access') as mock_assert_access:
            result = await set_course_emoji("course-123", mock_db, "user@test.com", 5)

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_personalization_service.set_course_emoji.assert_called_once_with(mock_course, mock_user, 5)
        mock_db.commit.assert_called_once()

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.CourseService')
    @patch('src.routers.personalization.PersonalizationService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_set_course_emoji_remove(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
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
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_user = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.personalization.CoursePolicy.assert_course_access'):
            result = await set_course_emoji("course-123", mock_db, "user@test.com", None)

        assert result.success is True
        mock_personalization_service.set_course_emoji.assert_called_once_with(mock_course, mock_user, None)

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_set_course_emoji_user_not_found(
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
            await set_course_emoji("course-123", mock_db, "user@test.com", 5)

        assert exc_info.value.status_code == 401

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.CourseService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_set_course_emoji_course_not_found(
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
            await set_course_emoji("course-123", mock_db, "user@test.com", 5)

        assert exc_info.value.status_code == 400

    @patch('src.routers.personalization.UserService')
    @patch('src.routers.personalization.CourseService')
    @patch('src.routers.personalization.get_db')
    @patch('src.routers.personalization.get_current_user')
    async def test_set_course_emoji_participant_role_required(
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
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.personalization.CoursePolicy.assert_course_access') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = course_errors.ParticipantRoleRequiredError("user@test.com", "course-123")
            await set_course_emoji("course-123", mock_db, "user@test.com", 5)

        assert exc_info.value.status_code == 403
