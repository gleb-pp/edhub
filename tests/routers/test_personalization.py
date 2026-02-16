from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import courses as course_errors
from src.exceptions import personalization as personalization_errors
from src.exceptions import users as user_errors
from src.routers.personalization import (
    change_courses_order,
    get_course_emoji,
    set_course_emoji,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user_service():
    with patch("src.routers.personalization.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service():
    with patch("src.routers.personalization.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_personalization_service():
    with patch("src.routers.personalization.PersonalizationService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user():
    with patch("src.routers.personalization.get_current_user") as mock_func:
        yield mock_func


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.email = "user@test.com"
    return user


@pytest.fixture
def mock_course():
    course = MagicMock()
    course.course_id = "course-123"
    return course


class TestPersonalizationRouter:

    async def test_get_course_emoji_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_user,
        mock_course,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_personalization_service.get_course_emoji.return_value = 5

        with patch("src.routers.personalization.CoursePolicy.assert_course_access") as mock_assert_access:
            result = await get_course_emoji(mock_db, mock_course.course_id, "user@test.com")

        assert result.emoji_id == 5
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_personalization_service.get_course_emoji.assert_called_once_with(mock_course, mock_user)

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policy",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("participant_role_required", course_errors.ParticipantRoleRequiredError("user@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "course_not_found", "participant_role_required"],
    )
    async def test_get_course_emoji_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policy,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with patch("src.routers.personalization.CoursePolicy.assert_course_access") as mock_assert_access:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "participant_role_required":
                    mock_assert_access.side_effect = side_effect

                await get_course_emoji(mock_db, mock_course.course_id, "user@test.com")

            assert exc_info.value.status_code == expected_status

            if should_check_policy:
                mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

        mock_personalization_service.get_course_emoji.assert_not_called()

    async def test_change_courses_order_success(
        self,
        mock_db,
        mock_user_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_user,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.return_value = mock_user

        new_order = ["course-1", "course-2", "course-3"]
        result = await change_courses_order(mock_db, new_order, "user@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_personalization_service.change_courses_order.assert_called_once_with(mock_user, new_order)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
            ("incorrect_order", personalization_errors.IncorrectCoursesOrderError(), 400),
        ],
        ids=["user_not_found", "incorrect_order"],
    )
    async def test_change_courses_order_errors(
        self,
        mock_db,
        mock_user_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_user,
        error_scenario,
        side_effect,
        expected_status,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user
            mock_personalization_service.change_courses_order.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            await change_courses_order(mock_db, ["course-1"], "user@test.com")

        assert exc_info.value.status_code == expected_status
        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        "emoji_id,expected_emoji",
        [
            (5, 5),
            (None, None),
        ],
        ids=["set_emoji", "remove_emoji"],
    )
    async def test_set_course_emoji_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        emoji_id,
        expected_emoji,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with patch("src.routers.personalization.CoursePolicy.assert_course_access") as mock_assert_access:
            result = await set_course_emoji(
                mock_course.course_id, mock_db, "user@test.com", emoji_id,
            )

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_personalization_service.set_course_emoji.assert_called_once_with(
            mock_course, mock_user, expected_emoji,
        )
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policy",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("participant_role_required", course_errors.ParticipantRoleRequiredError("user@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "course_not_found", "participant_role_required"],
    )
    async def test_set_course_emoji_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policy,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with patch("src.routers.personalization.CoursePolicy.assert_course_access") as mock_assert_access:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "participant_role_required":
                    mock_assert_access.side_effect = side_effect

                await set_course_emoji(mock_course.course_id, mock_db, "user@test.com", 5)

            assert exc_info.value.status_code == expected_status

            if should_check_policy:
                mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

        mock_personalization_service.set_course_emoji.assert_not_called()
        mock_db.commit.assert_not_called()
