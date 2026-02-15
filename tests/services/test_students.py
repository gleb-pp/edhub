from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from src.repo import Course, StudentAt, User
from src.services import StudentService


class TestStudentService:

    def test_get_enrolled_students_success(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        expected_students = [MagicMock(spec=User), MagicMock(spec=User)]
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = expected_students

        service = StudentService(mock_db)
        result = service.get_enrolled_students(mock_course)

        assert result == expected_students
        mock_db.query.assert_called_once_with(User)
        mock_query.join.assert_called_once()
        mock_join.filter.assert_called_once()
        mock_filter.order_by.assert_called_once()

    def test_get_enrolled_students_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = []

        service = StudentService(mock_db)
        result = service.get_enrolled_students(mock_course)

        assert result == []

    @patch.object(StudentService.logger, "info")
    def test_invite_student_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        service = StudentService(mock_db)
        service.invite_student(mock_student, mock_course)

        mock_db.add.assert_called_once()
        added_student_at = mock_db.add.call_args[0][0]
        assert isinstance(added_student_at, StudentAt)
        assert added_student_at.email == mock_student.email
        assert added_student_at.course_id == mock_course.course_id
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(StudentService.logger, "info")
    def test_remove_student_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        mock_student_at = MagicMock(spec=StudentAt)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_student_at

        service = StudentService(mock_db)
        service.remove_student(mock_student, mock_course)

        mock_db.query.assert_called_once_with(StudentAt)
        mock_query.filter.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_student_at)
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(StudentService.logger, "info")
    def test_remove_student_not_found_does_nothing(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        service = StudentService(mock_db)
        service.remove_student(mock_student, mock_course)

        mock_db.query.assert_called_once_with(StudentAt)
        mock_query.filter.assert_called_once()
        mock_db.delete.assert_not_called()
        mock_db.flush.assert_not_called()
