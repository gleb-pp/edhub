from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.repo import Course, ParentAt, User
from src.services import ParentService


class TestParentService:
    """Unit tests for ParentService methods."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Fixture for a mocked database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db: MagicMock) -> ParentService:
        """Fixture for the ParentService instance with a mocked database."""
        return ParentService(mock_db)

    @pytest.fixture
    def mock_parent(self) -> MagicMock:
        """Fixture for a mocked User instance representing a parent."""
        parent = MagicMock(spec=User)
        parent.email = "parent@test.com"
        return parent

    @pytest.fixture
    def mock_student(self) -> MagicMock:
        """Fixture for a mocked User instance representing a student."""
        student = MagicMock(spec=User)
        student.email = "student@test.com"
        return student

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        """Fixture for a mocked Course instance."""
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @patch.object(ParentService.logger, "info")
    def test_invite_parent(
        self,
        mock_logger: MagicMock,
        service: ParentService,
        mock_db: MagicMock,
        mock_parent: MagicMock,
        mock_student: MagicMock,
        mock_course: MagicMock,
    ) -> None:
        """Test that a parent is invited successfully, and that the ParentAt relationship is created correctly."""
        service.invite_parent(mock_parent, mock_student, mock_course)

        mock_db.add.assert_called_once()
        added_parent_at = mock_db.add.call_args[0][0]
        assert isinstance(added_parent_at, ParentAt)
        assert added_parent_at.parent_email == mock_parent.email
        assert added_parent_at.student_email == mock_student.email
        assert added_parent_at.course_id == mock_course.course_id
        mock_logger.assert_called_once()

    @pytest.mark.parametrize(
        ("existing", "should_delete"),
        [
            (MagicMock(spec=ParentAt), True),
            (None, False),
        ],
    )
    @patch.object(ParentService.logger, "info")
    def test_remove_parent_student(
        self,
        mock_logger: MagicMock,
        service: ParentService,
        mock_db: MagicMock,
        mock_parent: MagicMock,
        mock_student: MagicMock,
        mock_course: MagicMock,
        existing: MagicMock | None,
        should_delete: bool,
    ) -> None:
        """Test that a parent-student relationship is removed successfully, and that a warning is logged when the relationship is not found."""
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
        ("existing", "should_delete"),
        [
            (MagicMock(spec=ParentAt), True),
            (None, False),
        ],
    )
    @patch.object(ParentService.logger, "info")
    def test_remove_parent(
        self,
        mock_logger: MagicMock,
        service: ParentService,
        mock_db: MagicMock,
        mock_parent: MagicMock,
        mock_course: MagicMock,
        existing: MagicMock | None,
        should_delete: bool,
    ) -> None:
        """Test that a parent is removed successfully, and that a warning is logged when the parent is not found."""
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
        ("returned_value", "method_name"),
        [
            ([MagicMock(spec=User), MagicMock(spec=User)], "get_students_parents"),
            ([], "get_students_parents"),
            ([MagicMock(spec=User), MagicMock(spec=User)], "get_parents_children"),
            ([], "get_parents_children"),
        ],
    )
    def test_relationship_queries(
        self,
        service: ParentService,
        mock_db: MagicMock,
        mock_parent: MagicMock,
        mock_student: MagicMock,
        mock_course: MagicMock,
        returned_value: list[MagicMock],
        method_name: str,
    ) -> None:
        """Test that the correct relationships are queried successfully for both get_students_parents and get_parents_children methods."""
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
