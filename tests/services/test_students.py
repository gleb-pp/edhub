from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.repo import Course, StudentAt, User
from src.services import StudentService


class TestStudentService:

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db) -> StudentService:
        return StudentService(mock_db)

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @pytest.mark.parametrize("students_list", [
        ([MagicMock(spec=User), MagicMock(spec=User)]),
        ([]),
    ])
    def test_get_enrolled_students(self, service, mock_db, mock_course, students_list) -> None:
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = students_list

        result = service.get_enrolled_students(mock_course)
        assert result == students_list
        mock_db.query.assert_called_once_with(User)
        mock_query.join.assert_called_once()
        mock_join.filter.assert_called_once()
        mock_filter.order_by.assert_called_once()

    @patch.object(StudentService.logger, "info")
    def test_invite_student_success(self, mock_logger, service, mock_db, mock_course) -> None:
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"

        service.invite_student(mock_student, mock_course)

        mock_db.add.assert_called_once()
        added_student_at = mock_db.add.call_args[0][0]
        assert isinstance(added_student_at, StudentAt)
        assert added_student_at.email == mock_student.email
        assert added_student_at.course_id == mock_course.course_id
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(StudentService.logger, "info")
    @pytest.mark.parametrize("existing_student, should_delete", [
        (MagicMock(spec=StudentAt), True),
        (None, False),
    ])
    def test_remove_student(self, mock_logger, service, mock_db, mock_course, existing_student, should_delete) -> None:
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = existing_student

        if should_delete:
            service.remove_student(mock_student, mock_course)
            mock_db.query.assert_called_once_with(StudentAt)
            mock_query.filter.assert_called_once()
            mock_db.delete.assert_called_once_with(existing_student)
            mock_db.flush.assert_called_once()
            mock_logger.assert_called_once()
        else:
            service.remove_student(mock_student, mock_course)
            mock_db.query.assert_called_once_with(StudentAt)
            mock_query.filter.assert_called_once()
            mock_db.delete.assert_not_called()
            mock_db.flush.assert_not_called()
            mock_logger.assert_not_called()
