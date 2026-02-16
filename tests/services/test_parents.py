from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.repo import Course, ParentAt, User
from src.services import ParentService


class TestParentService:

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db) -> ParentService:
        return ParentService(mock_db)

    @pytest.fixture
    def mock_parent(self) -> MagicMock:
        parent = MagicMock(spec=User)
        parent.email = "parent@test.com"
        return parent

    @pytest.fixture
    def mock_student(self) -> MagicMock:
        student = MagicMock(spec=User)
        student.email = "student@test.com"
        return student

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @patch.object(ParentService.logger, "info")
    def test_invite_parent(self, mock_logger, service, mock_db, mock_parent, mock_student, mock_course) -> None:
        service.invite_parent(mock_parent, mock_student, mock_course)

        mock_db.add.assert_called_once()
        added_parent_at = mock_db.add.call_args[0][0]
        assert isinstance(added_parent_at, ParentAt)
        assert added_parent_at.parent_email == mock_parent.email
        assert added_parent_at.student_email == mock_student.email
        assert added_parent_at.course_id == mock_course.course_id
        mock_logger.assert_called_once()

    @pytest.mark.parametrize(
        "existing, should_delete",
        [
            (MagicMock(spec=ParentAt), True),
            (None, False),
        ],
    )
    @patch.object(ParentService.logger, "info")
    def test_remove_parent_student(
        self,
        mock_logger,
        service,
        mock_db,
        mock_parent,
        mock_student,
        mock_course,
        existing,
        should_delete,
    ) -> None:
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = existing

        service.remove_parent_student(mock_parent, mock_student, mock_course)

        mock_db.query.assert_called_once_with(ParentAt)
        mock_query.filter.assert_called_once()

        if should_delete:
            mock_db.delete.assert_called_once_with(existing)
            mock_db.flush.assert_called_once()
            mock_logger.assert_called_once()
        else:
            mock_db.delete.assert_not_called()
            mock_db.flush.assert_not_called()
            mock_logger.assert_not_called()

    @pytest.mark.parametrize(
        "existing, should_delete",
        [
            (MagicMock(spec=ParentAt), True),
            (None, False),
        ],
    )
    @patch.object(ParentService.logger, "info")
    def test_remove_parent(
        self,
        mock_logger,
        service,
        mock_db,
        mock_parent,
        mock_course,
        existing,
        should_delete,
    ) -> None:
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = existing

        service.remove_parent(mock_parent, mock_course)

        mock_db.query.assert_called_once_with(ParentAt)
        mock_query.filter.assert_called_once()
        if should_delete:
            mock_db.delete.assert_called_once_with(existing)
            mock_db.flush.assert_called_once()
            mock_logger.assert_called_once()
        else:
            mock_db.delete.assert_not_called()
            mock_db.flush.assert_not_called()
            mock_logger.assert_not_called()

    @pytest.mark.parametrize(
        "returned_value, method_name",
        [
            ([MagicMock(spec=User), MagicMock(spec=User)], "get_students_parents"),
            ([], "get_students_parents"),
            ([MagicMock(spec=User), MagicMock(spec=User)], "get_parents_children"),
            ([], "get_parents_children"),
        ],
    )
    def test_relationship_queries(
        self,
        service,
        mock_db,
        mock_parent,
        mock_student,
        mock_course,
        returned_value,
        method_name,
    ) -> None:
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_join.filter.return_value.all.return_value = returned_value

        if method_name == "get_students_parents":
            result = service.get_students_parents(mock_student, mock_course)
        else:
            result = service.get_parents_children(mock_parent, mock_course)

        assert result == returned_value
        mock_db.query.assert_called_once_with(User)
        mock_query.join.assert_called_once()
