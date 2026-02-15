from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from src.repo import Course, ParentAt, User
from src.services import ParentService


class TestParentService:

    @patch.object(ParentService.logger, "info")
    def test_invite_parent_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        service = ParentService(mock_db)
        service.invite_parent(mock_parent, mock_student, mock_course)

        mock_db.add.assert_called_once()
        added_parent_at = mock_db.add.call_args[0][0]
        assert isinstance(added_parent_at, ParentAt)
        assert added_parent_at.parent_email == mock_parent.email
        assert added_parent_at.student_email == mock_student.email
        assert added_parent_at.course_id == mock_course.course_id
        mock_logger.assert_called_once()

    @patch.object(ParentService.logger, "info")
    def test_remove_parent_student_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        mock_parent_at = MagicMock(spec=ParentAt)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_parent_at

        service = ParentService(mock_db)
        service.remove_parent_student(mock_parent, mock_student, mock_course)

        mock_db.query.assert_called_once_with(ParentAt)
        mock_query.filter.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_parent_at)
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(ParentService.logger, "info")
    def test_remove_parent_student_not_found_does_nothing(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        service = ParentService(mock_db)

        service.remove_parent_student(mock_parent, mock_student, mock_course)

        mock_db.query.assert_called_once_with(ParentAt)
        mock_query.filter.assert_called_once()
        mock_db.delete.assert_not_called()
        mock_db.flush.assert_not_called()

    @patch.object(ParentService.logger, "info")
    def test_remove_parent_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        mock_parent_at = MagicMock(spec=ParentAt)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_parent_at

        service = ParentService(mock_db)
        service.remove_parent(mock_parent, mock_course)

        mock_db.query.assert_called_once_with(ParentAt)
        mock_query.filter.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_parent_at)
        mock_logger.assert_called_once()

    @patch.object(ParentService.logger, "info")
    def test_remove_parent_not_found_does_nothing(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        service = ParentService(mock_db)

        service.remove_parent(mock_parent, mock_course)

        mock_db.query.assert_called_once_with(ParentAt)
        mock_query.filter.assert_called_once()
        mock_db.delete.assert_not_called()

    def test_get_students_parents_success(self):
        mock_db = MagicMock(spec=Session)
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        expected_parents = [MagicMock(spec=User), MagicMock(spec=User)]
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_filter.all.return_value = expected_parents

        service = ParentService(mock_db)
        result = service.get_students_parents(mock_student, mock_course)

        assert result == expected_parents
        mock_db.query.assert_called_once_with(User)
        mock_query.join.assert_called_once()

    def test_get_students_parents_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_student = MagicMock(spec=User)
        mock_student.email = "student@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_filter.all.return_value = []

        service = ParentService(mock_db)
        result = service.get_students_parents(mock_student, mock_course)

        assert result == []

    def test_get_parents_children_success(self):
        mock_db = MagicMock(spec=Session)
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        expected_children = [MagicMock(spec=User), MagicMock(spec=User)]
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_filter.all.return_value = expected_children

        service = ParentService(mock_db)
        result = service.get_parents_children(mock_parent, mock_course)

        assert result == expected_children
        mock_db.query.assert_called_once_with(User)
        mock_query.join.assert_called_once()

    def test_get_parents_children_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_parent = MagicMock(spec=User)
        mock_parent.email = "parent@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1

        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_filter.all.return_value = []

        service = ParentService(mock_db)
        result = service.get_parents_children(mock_parent, mock_course)

        assert result == []
