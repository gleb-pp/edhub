from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.exceptions import courses as course_errors
from src.services.courses import CourseService
from src.repo.courses import Course
from src.repo.personalization import PersonalCourseInfo
from src.repo.users import User


class TestCourseService:

    def test_get_course_success(self):
        mock_db = MagicMock(spec=Session)
        mock_query = mock_db.query.return_value
        expected_course = MagicMock(spec=Course)
        mock_query.filter.return_value.first.return_value = expected_course
        
        service = CourseService(mock_db)
        result = service.get_course("course-123")
        
        assert result == expected_course
        mock_db.query.assert_called_once_with(Course)
        mock_query.filter.assert_called_once()

    def test_get_course_not_found(self):
        mock_db = MagicMock(spec=Session)
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        service = CourseService(mock_db)
        
        with pytest.raises(course_errors.CourseNotFoundError) as exc_info:
            service.get_course("non-existent")
        
        assert "non-existent" in str(exc_info.value)

    def test_get_available_courses_success(self):
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "student@test.com"
        
        mock_query = mock_db.query.return_value
        expected_courses = [MagicMock(spec=Course), MagicMock(spec=Course)]
        mock_query.join.return_value.filter.return_value.order_by.return_value.all.return_value = expected_courses
        
        service = CourseService(mock_db)
        result = service.get_available_courses(mock_user)
        
        assert result == expected_courses
        mock_db.query.assert_called_once_with(Course)
        mock_query.join.assert_called_once()
        mock_query.join.return_value.filter.assert_called_once()

    def test_get_available_courses_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "student@test.com"
        
        mock_query = mock_db.query.return_value
        mock_query.join.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        service = CourseService(mock_db)
        result = service.get_available_courses(mock_user)
        
        assert result == []

    def test_get_all_courses_success(self):
        mock_db = MagicMock(spec=Session)
        expected_courses = [MagicMock(spec=Course), MagicMock(spec=Course)]
        mock_db.query.return_value.all.return_value = expected_courses
        
        service = CourseService(mock_db)
        result = service.get_all_courses()
        
        assert result == expected_courses
        mock_db.query.assert_called_once_with(Course)

    def test_get_all_courses_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.all.return_value = []
        
        service = CourseService(mock_db)
        result = service.get_all_courses()
        
        assert result == []

    @patch.object(CourseService.logger, 'info')
    def test_create_course_with_organization(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "instructor@test.com"
        
        service = CourseService(mock_db)
        result = service.create_course("Test Course", "Test Org", mock_user)
        
        assert isinstance(result, Course)
        assert result.title == "Test Course"
        assert result.organization == "Test Org"
        assert result.instructor == mock_user.email
        
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(CourseService.logger, 'info')
    def test_create_course_without_organization(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "instructor@test.com"
        
        service = CourseService(mock_db)
        result = service.create_course("Test Course", None, mock_user)
        
        assert isinstance(result, Course)
        assert result.title == "Test Course"
        assert result.organization is None
        assert result.instructor == mock_user.email
        
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(CourseService.logger, 'info')
    def test_create_course_empty_organization_string(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.email = "instructor@test.com"
        
        service = CourseService(mock_db)
        result = service.create_course("Test Course", "", mock_user)
        
        assert isinstance(result, Course)
        assert result.title == "Test Course"
        assert result.organization == ""
        assert result.instructor == mock_user.email

    def test_create_course_empty_title(self):
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        
        service = CourseService(mock_db)
        result = service.create_course("", None, mock_user)
        
        assert result.title == ""

    @patch.object(CourseService.logger, 'info')
    def test_delete_course_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        service = CourseService(mock_db)
        service.delete_course(mock_course)
        
        mock_db.delete.assert_called_once_with(mock_course)
        mock_logger.assert_called_once()
