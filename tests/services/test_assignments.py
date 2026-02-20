from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.assignments as assignment_errors
from src.repo import Course, CourseAssignment, CourseSection, User
from src.services import AssignmentService


class TestAssignmentService:
    """Unit tests for the AssignmentService class."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Fixture for a mocked database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db: MagicMock) -> AssignmentService:
        """Fixture for the AssignmentService instance with a mocked database."""
        return AssignmentService(mock_db)

    @pytest.fixture
    def mock_section(self) -> MagicMock:
        """Fixture for a mocked CourseSection."""
        section = MagicMock(spec=CourseSection)
        section.course_id = 1
        section.section_id = 2
        return section

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        """Fixture for a mocked Course."""
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @pytest.fixture
    def mock_author(self) -> MagicMock:
        """Fixture for a mocked User who is the author of an assignment."""
        author = MagicMock(spec=User)
        author.email = "teacher@test.com"
        return author

    @pytest.mark.parametrize(
        "returned_value",
        [
            [MagicMock(spec=CourseAssignment), MagicMock(spec=CourseAssignment)],
            [],
        ],
    )
    def test_get_section_assignments(
        self,
        service: AssignmentService,
        mock_db: MagicMock,
        mock_section: MagicMock,
        returned_value: list[MagicMock],
    ) -> None:
        """Test the get_section_assignments method with different returned values."""
        mock_db.query.return_value.filter.return_value.all.return_value = returned_value

        result = service.get_section_assignments(mock_section)

        assert result == returned_value
        mock_db.query.assert_called_once_with(CourseAssignment)

    @pytest.mark.parametrize(
        ("title", "description"),
        [
            ("Test Assignment", "Test Description"),
            ("", "Description"),
            ("Title", ""),
        ],
    )
    @patch.object(AssignmentService.logger, "info")
    def test_create_assignment(
        self,
        mock_logger: MagicMock,
        service: AssignmentService,
        mock_db: MagicMock,
        mock_section: MagicMock,
        mock_author: MagicMock,
        title: str,
        description: str,
    ) -> None:
        """Test the create_assignment method with different title and description values."""
        result = service.create_assignment(
            mock_section,
            title,
            description,
            mock_author,
        )

        assert isinstance(result, CourseAssignment)
        assert result.title == title
        assert result.description == description
        assert result.course_id == mock_section.course_id
        assert result.section_id == mock_section.section_id
        assert result.author == mock_author.email

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @pytest.mark.parametrize(
        ("assignment_id", "db_result", "should_raise"),
        [
            (10, MagicMock(spec=CourseAssignment), False),
            (999, None, True),
        ],
    )
    def test_get_assignment(
        self,
        service: AssignmentService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        assignment_id: int,
        db_result: MagicMock | None,
        should_raise: bool,
    ) -> None:
        """Test the get_assignment method with different assignment IDs and expected results."""
        mock_db.query.return_value.filter.return_value.first.return_value = db_result

        if should_raise:
            with pytest.raises(assignment_errors.AssignmentNotFoundError) as exc_info:
                service.get_assignment(mock_course, assignment_id)
            assert str(assignment_id) in str(exc_info.value)
            assert str(mock_course.course_id) in str(exc_info.value)
        else:
            result = service.get_assignment(mock_course, assignment_id)
            assert result == db_result
            mock_db.query.assert_called_once_with(CourseAssignment)

    @pytest.mark.parametrize(
        "returned_value",
        [
            [MagicMock(spec=CourseAssignment), MagicMock(spec=CourseAssignment)],
            [],
        ],
    )
    def test_get_course_assignments(
        self,
        service: AssignmentService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        returned_value: list[MagicMock],
    ) -> None:
        """Test the get_course_assignments method with different returned values."""
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = returned_value

        result = service.get_course_assignments(mock_course)

        assert result == returned_value
        mock_db.query.assert_called_once_with(CourseAssignment)

    @patch.object(AssignmentService.logger, "info")
    def test_delete_assignment(
        self,
        mock_logger: MagicMock,
        service: AssignmentService,
        mock_db: MagicMock,
    ) -> None:
        """Test the delete_assignment method to ensure it deletes the assignment and logs the action."""
        mock_assignment = MagicMock(spec=CourseAssignment)

        service.delete_assignment(mock_assignment)

        mock_db.delete.assert_called_once_with(mock_assignment)
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()
