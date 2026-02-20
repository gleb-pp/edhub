from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.courses as course_errors
import src.exceptions.personalization as personalization_errors
from src.repo import Course, PersonalCourseInfo, User
from src.services import PersonalizationService
from src.settings.course import course_settings


class TestPersonalizationService:
    """Unit tests for PersonalizationService methods."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Fixture for a mocked database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db: MagicMock) -> PersonalizationService:
        """Fixture for the PersonalizationService instance with a mocked database."""
        return PersonalizationService(mock_db)

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Fixture for a mocked User instance representing a course participant."""
        user = MagicMock(spec=User)
        user.email = "user@test.com"
        return user

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        """Fixture for a mocked Course instance."""
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @pytest.mark.parametrize(("max_order", "expected_order"), [(3, 4), (None, 1)])
    @patch.object(PersonalizationService.logger, "info")
    @patch("src.services.personalization.randbelow")
    def test_add_course_participant(
        self,
        mock_randbelow: MagicMock,
        mock_logger: MagicMock,
        service: PersonalizationService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        mock_user: MagicMock,
        max_order: int | None,
        expected_order: int,
    ) -> None:
        """Test that a course participant is added successfully."""
        mock_randbelow.return_value = 5
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.scalar.return_value = max_order

        service.add_course_participant(mock_course, mock_user)

        mock_db.add.assert_called_once()
        added_info = mock_db.add.call_args[0][0]
        assert isinstance(added_info, PersonalCourseInfo)
        assert added_info.course_id == mock_course.course_id
        assert added_info.email == mock_user.email
        assert added_info.emoji_id == 5
        assert added_info.course_order == expected_order
        mock_randbelow.assert_called_once_with(course_settings.emoji_count)
        mock_logger.assert_called_once()

    @pytest.mark.parametrize(("exists", "should_raise"), [(True, False), (False, True)])
    @patch.object(PersonalizationService.logger, "info")
    @patch.object(PersonalizationService.logger, "warning")
    def test_remove_course_participant(
        self,
        mock_warning: MagicMock,
        mock_info: MagicMock,
        service: PersonalizationService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        mock_user: MagicMock,
        exists: bool,
        should_raise: bool,
    ) -> None:
        """Test that a course participant is removed successfully."""
        mock_personal_info = MagicMock(spec=PersonalCourseInfo) if exists else None
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_personal_info

        if should_raise:
            with pytest.raises(course_errors.ParticipantRoleRequiredError):
                service.remove_course_participant(mock_course, mock_user)
            mock_warning.assert_called_once()
            mock_db.delete.assert_not_called()
            mock_info.assert_not_called()
        else:
            service.remove_course_participant(mock_course, mock_user)
            mock_db.query.assert_called_once_with(PersonalCourseInfo)
            mock_query.filter.assert_called_once()
            mock_db.delete.assert_called_once_with(mock_personal_info)
            mock_info.assert_called_once()
            mock_warning.assert_not_called()

    @pytest.mark.parametrize(("exists", "expected_emoji"), [(True, 7), (False, None)])
    @patch.object(PersonalizationService.logger, "warning")
    def test_get_course_emoji(
        self,
        mock_warning: MagicMock,
        service: PersonalizationService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        mock_user: MagicMock,
        exists: bool,
        expected_emoji: int | None,
    ) -> None:
        """Test that the course emoji is retrieved successfully."""
        mock_personal_info = MagicMock(spec=PersonalCourseInfo) if exists else None
        if exists:
            mock_personal_info.emoji_id = 7
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_personal_info

        if exists:
            result = service.get_course_emoji(mock_course, mock_user)
            assert result == expected_emoji
            mock_warning.assert_not_called()
        else:
            with pytest.raises(course_errors.ParticipantRoleRequiredError):
                service.get_course_emoji(mock_course, mock_user)
            mock_warning.assert_called_once()

    @pytest.mark.parametrize(("new_order", "should_raise"), [
        (["course-2", "course-1"], False),
        (["course-1"], True),
        (["course-1", "course-3"], True),
    ])
    @patch.object(PersonalizationService.logger, "info")
    @patch.object(PersonalizationService.logger, "warning")
    def test_change_courses_order(
        self,
        mock_warning: MagicMock,
        mock_info: MagicMock,
        service: PersonalizationService,
        mock_db: MagicMock,
        mock_user: MagicMock,
        new_order: list[str],
        should_raise: bool,
    ) -> None:
        """Test that the courses order is changed successfully."""
        mock_course1 = MagicMock(spec=PersonalCourseInfo)
        mock_course1.course_id = "course-1"
        mock_course2 = MagicMock(spec=PersonalCourseInfo)
        mock_course2.course_id = "course-2"
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = [mock_course1, mock_course2]
        mock_db.query.side_effect = lambda x: mock_query if x == PersonalCourseInfo else MagicMock()

        if should_raise:
            with pytest.raises(personalization_errors.IncorrectCoursesOrderError):
                service.change_courses_order(mock_user, new_order)
            mock_warning.assert_called_once()
        else:
            service.change_courses_order(mock_user, new_order)
            assert mock_db.query.call_count == 3
            mock_info.assert_called_once()
            mock_warning.assert_not_called()

    @pytest.mark.parametrize(("emoji_input", "expected_value"), [(5, 5), (None, None)])
    @patch.object(PersonalizationService.logger, "info")
    @patch.object(PersonalizationService.logger, "warning")
    def test_set_course_emoji(
        self,
        mock_warning: MagicMock,
        mock_info: MagicMock,
        service: PersonalizationService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        mock_user: MagicMock,
        emoji_input: int | None,
        expected_value: int | None,
    ) -> None:
        """Test that the course emoji is set successfully."""
        mock_personal_info = MagicMock(spec=PersonalCourseInfo)
        mock_personal_info.emoji_id = 3
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_personal_info

        service.set_course_emoji(mock_course, mock_user, emoji_input)
        assert mock_personal_info.emoji_id == expected_value
        mock_info.assert_called_once()
        mock_warning.assert_not_called()

    @patch.object(PersonalizationService.logger, "info")
    @patch.object(PersonalizationService.logger, "warning")
    def test_set_course_emoji_not_found(
        self,
        mock_warning: MagicMock,
        mock_info: MagicMock,
        service: PersonalizationService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test that a warning is logged when trying to set the course emoji for a participant whose personalization info is not found."""
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        with pytest.raises(course_errors.ParticipantRoleRequiredError):
            service.set_course_emoji(mock_course, mock_user, 5)
        mock_warning.assert_called_once()
        mock_info.assert_called_once()
