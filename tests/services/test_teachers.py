from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.repo import Course, Teaches, User
from src.services import TeacherService


class TestTeacherService:

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db) -> TeacherService:
        return TeacherService(mock_db)

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @pytest.fixture
    def mock_teacher(self) -> MagicMock:
        teacher = MagicMock(spec=User)
        teacher.email = "teacher@test.com"
        return teacher

    @pytest.mark.parametrize(
        ("existing_teachers", "expected_count"),
        [
            ([MagicMock(spec=User), MagicMock(spec=User)], 2),
            ([], 0),
        ],
    )
    def test_get_course_teachers(self, service, mock_db, mock_course, existing_teachers, expected_count) -> None:
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = existing_teachers

        result = service.get_course_teachers(mock_course)
        assert len(result) == expected_count
        mock_db.query.assert_called_once_with(User)
        if expected_count > 0:
            mock_query.join.assert_called_once()
            mock_join.filter.assert_called_once()
            mock_filter.order_by.assert_called_once()

    @patch.object(TeacherService.logger, "info")
    def test_change_course_instructor(self, mock_logger, service, mock_db) -> None:
        old_instructor = MagicMock(spec=User)
        old_instructor.email = "old@test.com"
        new_teacher = MagicMock(spec=User)
        new_teacher.email = "new@test.com"

        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_course.instructor = old_instructor.email

        mock_teaches = MagicMock(spec=Teaches)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_teaches

        service.change_course_instructor(old_instructor, new_teacher, mock_course)
        assert mock_course.instructor == new_teacher.email
        mock_db.delete.assert_called_once_with(mock_teaches)
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert mock_logger.call_count == 3

    @patch.object(TeacherService.logger, "info")
    def test_change_course_instructor_same_person(self, mock_logger, service, mock_db) -> None:
        old_instructor = MagicMock(spec=User)
        old_instructor.email = "same@test.com"
        new_teacher = MagicMock(spec=User)
        new_teacher.email = "same@test.com"

        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_course.instructor = old_instructor.email

        mock_teaches = MagicMock(spec=Teaches)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_teaches

        service.change_course_instructor(old_instructor, new_teacher, mock_course)

        assert mock_course.instructor == new_teacher.email
        mock_db.delete.assert_called_once_with(mock_teaches)
        mock_db.add.assert_not_called()
        mock_db.flush.assert_called_once()
        assert mock_logger.call_count == 2
