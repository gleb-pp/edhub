from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.sections as section_errors
from src.repo import Course, CourseSection
from src.services import SectionService


class TestSectionService:
    """Unit tests for SectionService methods."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Fixture for a mocked database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db: MagicMock) -> SectionService:
        """Fixture for the SectionService instance with a mocked database."""
        return SectionService(mock_db)

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        """Fixture for a mocked Course instance."""
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @pytest.mark.parametrize("sections_list", [
        ([MagicMock(spec=CourseSection), MagicMock(spec=CourseSection)]),
        ([]),
    ])
    def test_get_course_sections(
        self,
        service: SectionService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        sections_list: list[MagicMock],
    ) -> None:
        """Test that sections for a course are retrieved successfully."""
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = sections_list

        result = service.get_course_sections(mock_course)
        assert result == sections_list
        mock_db.query.assert_called_once_with(CourseSection)
        mock_query.filter.assert_called_once()

    @pytest.mark.parametrize(("existing", "should_raise"), [
        (MagicMock(spec=CourseSection), False),
        (None, True),
    ])
    @patch.object(SectionService.logger, "warning")
    def test_get_section(
        self,
        mock_logger: MagicMock,
        service: SectionService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        existing: MagicMock | None,
        should_raise: bool,
    ) -> None:
        """Test that a section is retrieved successfully, and that a warning is logged when the section is not found."""
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = existing

        if should_raise:
            with pytest.raises(section_errors.SectionNotFoundError):
                service.get_section(mock_course, 999)
            mock_logger.assert_called_once()
        else:
            result = service.get_section(mock_course, 5)
            assert result == existing
            mock_db.query.assert_called_once_with(CourseSection)
            mock_query.filter.assert_called_once()
            mock_logger.assert_not_called()

    @pytest.mark.parametrize(("max_order", "expected_order"), [(3, 4), (None, 1)])
    @patch.object(SectionService.logger, "info")
    def test_create_section(
        self,
        mock_logger: MagicMock,
        service: SectionService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        max_order: int | None,
        expected_order: int,
    ) -> None:
        """Test that a section is created successfully, and that the section order is set correctly based on existing sections."""
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.scalar.return_value = max_order

        result = service.create_section("New Section", mock_course)
        assert isinstance(result, CourseSection)
        assert result.course_id == mock_course.course_id
        assert result.section_order == expected_order

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    def test_create_section_empty_title(
        self,
        service: SectionService,
        mock_db: MagicMock,
        mock_course: MagicMock,
    ) -> None:
        """Test that a section is created successfully with an empty title."""
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.scalar.return_value = 0

        result = service.create_section("", mock_course)
        assert result.title == ""

    @pytest.mark.parametrize(("existing_sections", "should_raise"), [(3, False), (1, True)])
    @patch.object(SectionService.logger, "info")
    def test_remove_section(
        self,
        mock_logger: MagicMock,
        service: SectionService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        existing_sections: int,
        should_raise: bool,
    ) -> None:
        """Test that a section is removed successfully, and that an error is raised when trying to remove the last remaining section."""
        mock_section = MagicMock(spec=CourseSection)
        mock_section.section_id = 5
        mock_section.course_id = 1

        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.scalar.return_value = existing_sections

        if should_raise:
            with pytest.raises(section_errors.LastSectionDeleteError):
                service.remove_section(mock_section)
            mock_db.delete.assert_not_called()
        else:
            service.remove_section(mock_section)
            mock_db.delete.assert_called_once_with(mock_section)
            mock_logger.assert_called_once()

    @pytest.mark.parametrize(("new_order", "should_raise"), [
        ([103, 101, 102], False),
        ([101], True),
        ([101, 103], True),
    ])
    @patch.object(SectionService.logger, "info")
    @patch.object(SectionService.logger, "warning")
    def test_change_section_order(
        self,
        mock_warning: MagicMock,
        mock_info: MagicMock,
        service: SectionService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        new_order: list[int],
        should_raise: bool,
    ) -> None:
        """Test that the section order is changed successfully, and that a warning is logged when the new order is invalid."""
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

        mock_db.query.side_effect = lambda x: mock_query if x == CourseSection else MagicMock()

        if should_raise:
            with pytest.raises(section_errors.IncorrectSectionOrderError):
                service.change_section_order(mock_course, new_order)
            mock_warning.assert_called_once()
        else:
            service.change_section_order(mock_course, new_order)
            assert mock_db.query.call_count >= 1
            mock_info.assert_called_once()
            mock_warning.assert_not_called()
