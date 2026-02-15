from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.sections as section_errors
from src.services import SectionService
from src.repo import Course, CourseSection


class TestSectionService:

    def test_get_course_sections_success(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        expected_sections = [MagicMock(spec=CourseSection), MagicMock(spec=CourseSection)]
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = expected_sections
        
        service = SectionService(mock_db)
        result = service.get_course_sections(mock_course)
        
        assert result == expected_sections
        mock_db.query.assert_called_once_with(CourseSection)
        mock_query.filter.assert_called_once()

    def test_get_course_sections_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = []
        
        service = SectionService(mock_db)
        result = service.get_course_sections(mock_course)
        
        assert result == []

    def test_get_section_success(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        expected_section = MagicMock(spec=CourseSection)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = expected_section
        
        service = SectionService(mock_db)
        result = service.get_section(mock_course, 5)
        
        assert result == expected_section
        mock_db.query.assert_called_once_with(CourseSection)
        mock_query.filter.assert_called_once()

    @patch.object(SectionService.logger, 'warning')
    def test_get_section_not_found(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        service = SectionService(mock_db)
        
        with pytest.raises(section_errors.SectionNotFoundError) as exc_info:
            service.get_section(mock_course, 999)
        
        assert "999" in str(exc_info.value)
        assert "1" in str(exc_info.value)
        mock_logger.assert_called_once()

    @patch.object(SectionService.logger, 'info')
    def test_create_section_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_max_order_query = mock_db.query.return_value
        mock_max_order_query.filter.return_value.scalar.return_value = 3
        
        service = SectionService(mock_db)
        result = service.create_section("New Section", mock_course)
        
        assert isinstance(result, CourseSection)
        assert result.course_id == mock_course.course_id
        assert result.title == "New Section"
        assert result.section_order == 4
        
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(SectionService.logger, 'info')
    def test_create_section_first_section(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_max_order_query = mock_db.query.return_value
        mock_max_order_query.filter.return_value.scalar.return_value = None
        
        service = SectionService(mock_db)
        result = service.create_section("First Section", mock_course)
        
        assert result.section_order == 1

    def test_create_section_empty_title(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_max_order_query = mock_db.query.return_value
        mock_max_order_query.filter.return_value.scalar.return_value = 0
        
        service = SectionService(mock_db)
        result = service.create_section("", mock_course)
        
        assert result.title == ""

    @patch.object(SectionService.logger, 'info')
    def test_remove_section_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_section.section_id = 5
        mock_section.course_id = 1
        
        mock_count_query = mock_db.query.return_value
        mock_count_query.filter.return_value.scalar.return_value = 3
        
        service = SectionService(mock_db)
        service.remove_section(mock_section)
        
        mock_db.delete.assert_called_once_with(mock_section)
        mock_logger.assert_called_once()

    @patch.object(SectionService.logger, 'info')
    def test_remove_section_last_section_error(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_section.section_id = 5
        mock_section.course_id = 1
        
        mock_count_query = mock_db.query.return_value
        mock_count_query.filter.return_value.scalar.return_value = 1
        
        service = SectionService(mock_db)
        
        with pytest.raises(section_errors.LastSectionDeleteError) as exc_info:
            service.remove_section(mock_section)
        
        assert str(mock_section.section_id) in str(exc_info.value)
        assert str(mock_section.course_id) in str(exc_info.value)
        mock_db.delete.assert_not_called()

    @patch.object(SectionService.logger, 'info')
    @patch.object(SectionService.logger, 'warning')
    def test_change_section_order_success(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_section1 = MagicMock(spec=CourseSection)
        mock_section1.section_id = 101
        mock_section2 = MagicMock(spec=CourseSection)
        mock_section2.section_id = 102
        mock_section3 = MagicMock(spec=CourseSection)
        mock_section3.section_id = 103
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = [mock_section1, mock_section2, mock_section3]
        
        def query_side_effect(*args):
            if args[0] == CourseSection:
                return mock_query
            return MagicMock()
        
        mock_db.query.side_effect = query_side_effect
        
        new_order = [103, 101, 102]
        
        service = SectionService(mock_db)
        service.change_section_order(mock_course, new_order)
        
        assert mock_db.query.call_count == 4
        mock_info.assert_called_once()
        mock_warning.assert_not_called()

    @patch.object(SectionService.logger, 'info')
    @patch.object(SectionService.logger, 'warning')
    def test_change_section_order_wrong_length(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_section1 = MagicMock(spec=CourseSection)
        mock_section1.section_id = 101
        mock_section2 = MagicMock(spec=CourseSection)
        mock_section2.section_id = 102
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = [mock_section1, mock_section2]
        
        new_order = [101]
        
        service = SectionService(mock_db)
        
        with pytest.raises(section_errors.IncorrectSectionOrderError):
            service.change_section_order(mock_course, new_order)
        
        mock_warning.assert_called_once()

    @patch.object(SectionService.logger, 'info')
    @patch.object(SectionService.logger, 'warning')
    def test_change_section_order_wrong_set(self, mock_warning, mock_info):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_section1 = MagicMock(spec=CourseSection)
        mock_section1.section_id = 101
        mock_section2 = MagicMock(spec=CourseSection)
        mock_section2.section_id = 102
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = [mock_section1, mock_section2]
        
        new_order = [101, 103]
        
        service = SectionService(mock_db)
        
        with pytest.raises(section_errors.IncorrectSectionOrderError):
            service.change_section_order(mock_course, new_order)
        
        mock_warning.assert_called_once()
