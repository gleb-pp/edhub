from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.assignments as assignment_errors
from src.services.assignments import AssignmentService
from src.repo.assignments import CourseAssignment
from src.repo.courses import Course
from src.repo.sections import CourseSection
from src.repo.users import User


class TestAssignmentService:

    def test_get_section_assignments_success(self):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_section.course_id = 1
        mock_section.section_id = 2
        
        mock_query = mock_db.query.return_value
        expected_assignments = [MagicMock(spec=CourseAssignment), MagicMock(spec=CourseAssignment)]
        mock_query.filter.return_value.all.return_value = expected_assignments
        
        service = AssignmentService(mock_db)
        result = service.get_section_assignments(mock_section)
        
        assert result == expected_assignments
        mock_db.query.assert_called_once_with(CourseAssignment)
        mock_query.filter.assert_called_once()

    def test_get_section_assignments_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_section.course_id = 1
        mock_section.section_id = 2
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = []
        
        service = AssignmentService(mock_db)
        result = service.get_section_assignments(mock_section)
        
        assert result == []

    @patch.object(AssignmentService.logger, 'info')
    def test_create_assignment_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_section.course_id = 1
        mock_section.section_id = 2
        mock_author = MagicMock(spec=User)
        mock_author.email = "teacher@test.com"
        
        service = AssignmentService(mock_db)
        result = service.create_assignment(mock_section, "Test Assignment", "Test Description", mock_author)
        
        assert isinstance(result, CourseAssignment)
        assert result.course_id == mock_section.course_id
        assert result.section_id == mock_section.section_id
        assert result.author == mock_author.email
        assert result.title == "Test Assignment"
        assert result.description == "Test Description"
        
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    def test_create_assignment_empty_title(self):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_author = MagicMock(spec=User)
        
        service = AssignmentService(mock_db)
        result = service.create_assignment(mock_section, "", "Description", mock_author)
        
        assert result.title == ""

    def test_create_assignment_empty_description(self):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_author = MagicMock(spec=User)
        
        service = AssignmentService(mock_db)
        result = service.create_assignment(mock_section, "Title", "", mock_author)
        
        assert result.description == ""

    def test_get_assignment_success(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        expected_assignment = MagicMock(spec=CourseAssignment)
        mock_query.filter.return_value.first.return_value = expected_assignment
        
        service = AssignmentService(mock_db)
        result = service.get_assignment(mock_course, 10)
        
        assert result == expected_assignment
        mock_db.query.assert_called_once_with(CourseAssignment)
        mock_query.filter.assert_called_once()

    def test_get_assignment_not_found(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        service = AssignmentService(mock_db)
        
        with pytest.raises(assignment_errors.AssignmentNotFoundError) as exc_info:
            service.get_assignment(mock_course, 999)
        
        assert "999" in str(exc_info.value)
        assert "1" in str(exc_info.value)

    def test_get_course_assignments_success(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        expected_assignments = [MagicMock(spec=CourseAssignment), MagicMock(spec=CourseAssignment)]
        mock_query.join.return_value.filter.return_value.order_by.return_value.all.return_value = expected_assignments
        
        service = AssignmentService(mock_db)
        result = service.get_course_assignments(mock_course)
        
        assert result == expected_assignments
        mock_db.query.assert_called_once_with(CourseAssignment)
        mock_query.join.assert_called_once()

    def test_get_course_assignments_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        mock_query.join.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        service = AssignmentService(mock_db)
        result = service.get_course_assignments(mock_course)
        
        assert result == []

    @patch.object(AssignmentService.logger, 'info')
    def test_delete_assignment_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_assignment = MagicMock(spec=CourseAssignment)
        mock_assignment.assignment_id = 10
        mock_assignment.course_id = 1
        
        service = AssignmentService(mock_db)
        service.delete_assignment(mock_assignment)
        
        mock_db.delete.assert_called_once_with(mock_assignment)
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()
