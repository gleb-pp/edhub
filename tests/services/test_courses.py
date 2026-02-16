import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from src.exceptions import courses as course_errors
from src.repo import Course, User
from src.services import CourseService


class TestCourseService:

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        return CourseService(mock_db)

    @pytest.fixture
    def mock_user(self):
        user = MagicMock(spec=User)
        user.email = "student@test.com"
        return user

    @pytest.mark.parametrize(
        "db_result, should_raise",
        [
            (MagicMock(spec=Course), False),
            (None, True),
        ],
    )
    def test_get_course(self, service, mock_db, db_result, should_raise):
        mock_db.query.return_value.filter.return_value.first.return_value = db_result

        if should_raise:
            with pytest.raises(course_errors.CourseNotFoundError) as exc_info:
                service.get_course("course-123")
            assert "course-123" in str(exc_info.value)
        else:
            result = service.get_course("course-123")
            assert result == db_result
            mock_db.query.assert_called_once_with(Course)

    @pytest.mark.parametrize(
        "returned_value",
        [
            [MagicMock(spec=Course), MagicMock(spec=Course)],
            [],
        ],
    )
    def test_get_available_courses(self, service, mock_db, mock_user, returned_value):
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = returned_value

        result = service.get_available_courses(mock_user)

        assert result == returned_value
        mock_db.query.assert_called_once_with(Course)

    @pytest.mark.parametrize(
        "returned_value",
        [
            [MagicMock(spec=Course), MagicMock(spec=Course)],
            [],
        ],
    )
    def test_get_all_courses(self, service, mock_db, returned_value):
        mock_db.query.return_value.all.return_value = returned_value

        result = service.get_all_courses()

        assert result == returned_value
        mock_db.query.assert_called_once_with(Course)

    @pytest.mark.parametrize(
        "organization",
        [
            "Test Org",
            None,
            "",
        ],
    )
    @patch.object(CourseService.logger, "info")
    def test_create_course(self, mock_logger, service, mock_db, organization):
        mock_user = MagicMock(spec=User)
        mock_user.email = "instructor@test.com"

        result = service.create_course("Test Course", organization, mock_user)

        assert isinstance(result, Course)
        assert result.title == "Test Course"
        assert result.organization == organization
        assert result.instructor == mock_user.email

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    def test_create_course_empty_title(self, service):
        mock_user = MagicMock(spec=User)
        result = service.create_course("", None, mock_user)
        assert result.title == ""

    @patch.object(CourseService.logger, "info")
    def test_delete_course(self, mock_logger, service, mock_db):
        mock_course = MagicMock(spec=Course)

        service.delete_course(mock_course)

        mock_db.delete.assert_called_once_with(mock_course)
        mock_logger.assert_called_once()
