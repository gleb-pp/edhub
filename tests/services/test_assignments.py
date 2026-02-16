import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

import src.exceptions.assignments as assignment_errors
from src.repo import Course, CourseAssignment, CourseSection, User
from src.services import AssignmentService


class TestAssignmentService:

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        return AssignmentService(mock_db)

    @pytest.fixture
    def mock_section(self):
        section = MagicMock(spec=CourseSection)
        section.course_id = 1
        section.section_id = 2
        return section

    @pytest.fixture
    def mock_course(self):
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @pytest.fixture
    def mock_author(self):
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
    def test_get_section_assignments(self, service, mock_db, mock_section, returned_value):
        mock_db.query.return_value.filter.return_value.all.return_value = returned_value

        result = service.get_section_assignments(mock_section)

        assert result == returned_value
        mock_db.query.assert_called_once_with(CourseAssignment)

    @pytest.mark.parametrize(
        "title, description",
        [
            ("Test Assignment", "Test Description"),
            ("", "Description"),
            ("Title", ""),
        ],
    )
    @patch.object(AssignmentService.logger, "info")
    def test_create_assignment(
        self,
        mock_logger,
        service,
        mock_db,
        mock_section,
        mock_author,
        title,
        description,
    ):
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
        "assignment_id, db_result, should_raise",
        [
            (10, MagicMock(spec=CourseAssignment), False),
            (999, None, True),
        ],
    )
    def test_get_assignment(self, service, mock_db, mock_course, assignment_id, db_result, should_raise):
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
    def test_get_course_assignments(self, service, mock_db, mock_course, returned_value):
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = returned_value

        result = service.get_course_assignments(mock_course)

        assert result == returned_value
        mock_db.query.assert_called_once_with(CourseAssignment)

    @patch.object(AssignmentService.logger, "info")
    def test_delete_assignment(self, mock_logger, service, mock_db):
        mock_assignment = MagicMock(spec=CourseAssignment)

        service.delete_assignment(mock_assignment)

        mock_db.delete.assert_called_once_with(mock_assignment)
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()
