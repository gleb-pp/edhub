from unittest.mock import MagicMock, patch
from secrets import randbelow

import pytest
from sqlalchemy.orm import Session

import src.exceptions.courses as course_errors
import src.exceptions.personalization as personalization_errors
from src.services.personalization import PersonalizationService
from src.repo.courses import Course
from src.repo.personalization import PersonalCourseInfo
from src.repo.users import User
from src.settings.course import course_settings


class TestPersonalizationService:

    @patch.object(PersonalizationService.logger, 'info')
    @patch('src.services.personalization.randbelow')
    def test_add_course_participant_success(self, mock_randbelow, mock_logger):
        mock_randbelow.return_value = 5
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_max_order_query = mock_db.query.return_value
        mock_max_order_query.filter.return_value.scalar.return_value = 3
        
        service = PersonalizationService(mock_db)
        service.add_course_participant(mock_course, mock_user)
        
        mock_db.add.assert_called_once()
        added_info = mock_db.add.call_args[0][0]
        assert isinstance(added_info, PersonalCourseInfo)
        assert added_info.course_id == mock_course.course_id
        assert added_info.email == mock_user.email
        assert added_info.emoji_id == 5
        assert added_info.course_order == 4
        mock_randbelow.assert_called_once_with(course_settings.emoji_count)
        mock_logger.assert_called_once()

    @patch.object(PersonalizationService.logger, 'info')
    @patch('src.services.personalization.randbelow')
    def test_add_course_participant_first_course(self, mock_randbelow, mock_logger):
        mock_randbelow.return_value = 3
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_max_order_query = mock_db.query.return_value
        mock_max_order_query.filter.return_value.scalar.return_value = None
        
        service = PersonalizationService(mock_db)
        service.add_course_participant(mock_course, mock_user)
        
        added_info = mock_db.add.call_args[0][0]
        assert added_info.course_order == 1

    @patch.object(PersonalizationService.logger, 'info')
    @patch.object(PersonalizationService.logger, 'warning')
    def test_remove_course_participant_success(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_personal_info = MagicMock(spec=PersonalCourseInfo)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_personal_info
        
        service = PersonalizationService(mock_db)
        service.remove_course_participant(mock_course, mock_user)
        
        mock_db.query.assert_called_once_with(PersonalCourseInfo)
        mock_query.filter.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_personal_info)
        mock_info.assert_called_once()
        mock_warning.assert_not_called()

    @patch.object(PersonalizationService.logger, 'info')
    @patch.object(PersonalizationService.logger, 'warning')
    def test_remove_course_participant_not_found(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        service = PersonalizationService(mock_db)
        
        with pytest.raises(course_errors.ParticipantRoleRequiredError) as exc_info:
            service.remove_course_participant(mock_course, mock_user)
        
        assert mock_user.email in str(exc_info.value)
        assert str(mock_course.course_id) in str(exc_info.value)
        mock_warning.assert_called_once()
        mock_db.delete.assert_not_called()

    @patch.object(PersonalizationService.logger, 'warning')
    def test_get_course_emoji_success(self, mock_warning):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_personal_info = MagicMock(spec=PersonalCourseInfo)
        mock_personal_info.emoji_id = 7
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_personal_info
        
        service = PersonalizationService(mock_db)
        result = service.get_course_emoji(mock_course, mock_user)
        
        assert result == 7
        mock_warning.assert_not_called()

    @patch.object(PersonalizationService.logger, 'warning')
    def test_get_course_emoji_not_found(self, mock_warning):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        service = PersonalizationService(mock_db)
        
        with pytest.raises(course_errors.ParticipantRoleRequiredError) as exc_info:
            service.get_course_emoji(mock_course, mock_user)
        
        mock_warning.assert_called_once()

    @patch.object(PersonalizationService.logger, 'info')
    @patch.object(PersonalizationService.logger, 'warning')
    def test_change_courses_order_success(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_course1 = MagicMock(spec=PersonalCourseInfo)
        mock_course1.course_id = "course-1"
        mock_course2 = MagicMock(spec=PersonalCourseInfo)
        mock_course2.course_id = "course-2"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = [mock_course1, mock_course2]
        
        def query_side_effect(*args):
            if args[0] == PersonalCourseInfo:
                return mock_query
            return MagicMock()
        
        mock_db.query.side_effect = query_side_effect
        
        new_order = ["course-2", "course-1"]
        
        service = PersonalizationService(mock_db)
        service.change_courses_order(mock_user, new_order)
        
        assert mock_db.query.call_count == 3
        mock_info.assert_called_once()
        mock_warning.assert_not_called()

    @patch.object(PersonalizationService.logger, 'info')
    @patch.object(PersonalizationService.logger, 'warning')
    def test_change_courses_order_wrong_length(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_course1 = MagicMock(spec=PersonalCourseInfo)
        mock_course1.course_id = "course-1"
        mock_course2 = MagicMock(spec=PersonalCourseInfo)
        mock_course2.course_id = "course-2"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = [mock_course1, mock_course2]
        
        new_order = ["course-1"]
        
        service = PersonalizationService(mock_db)
        
        with pytest.raises(personalization_errors.IncorrectCoursesOrderError):
            service.change_courses_order(mock_user, new_order)
        
        mock_warning.assert_called_once()

    @patch.object(PersonalizationService.logger, 'info')
    @patch.object(PersonalizationService.logger, 'warning')
    def test_change_courses_order_wrong_set(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_course1 = MagicMock(spec=PersonalCourseInfo)
        mock_course1.course_id = "course-1"
        mock_course2 = MagicMock(spec=PersonalCourseInfo)
        mock_course2.course_id = "course-2"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = [mock_course1, mock_course2]
        
        new_order = ["course-1", "course-3"]
        
        service = PersonalizationService(mock_db)
        
        with pytest.raises(personalization_errors.IncorrectCoursesOrderError):
            service.change_courses_order(mock_user, new_order)
        
        mock_warning.assert_called_once()

    @patch.object(PersonalizationService.logger, 'info')
    @patch.object(PersonalizationService.logger, 'warning')
    def test_set_course_emoji_success(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_personal_info = MagicMock(spec=PersonalCourseInfo)
        mock_personal_info.emoji_id = 3
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_personal_info
        
        service = PersonalizationService(mock_db)
        service.set_course_emoji(mock_course, mock_user, 5)
        
        assert mock_personal_info.emoji_id == 5
        mock_info.assert_called_once()
        mock_warning.assert_not_called()

    @patch.object(PersonalizationService.logger, 'info')
    @patch.object(PersonalizationService.logger, 'warning')
    def test_set_course_emoji_remove_emoji(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_personal_info = MagicMock(spec=PersonalCourseInfo)
        mock_personal_info.emoji_id = 3
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_personal_info
        
        service = PersonalizationService(mock_db)
        service.set_course_emoji(mock_course, mock_user, None)
        
        assert mock_personal_info.emoji_id is None

    @patch.object(PersonalizationService.logger, 'info')
    @patch.object(PersonalizationService.logger, 'warning')
    def test_set_course_emoji_not_found(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_user = MagicMock(spec=User)
        mock_user.email = "user@test.com"
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        service = PersonalizationService(mock_db)
        
        with pytest.raises(course_errors.ParticipantRoleRequiredError) as exc_info:
            service.set_course_emoji(mock_course, mock_user, 5)
        
        mock_warning.assert_called_once()
        mock_info.assert_called_once()
