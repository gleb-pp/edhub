from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.materials as material_errors
from src.repo import Course, CourseMaterial, CourseSection, User
from src.services import MaterialService


class TestMaterialService:
    """Unit tests for MaterialService methods."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Fixture for a mocked database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db: MagicMock) -> MaterialService:
        """Fixture for the MaterialService instance with a mocked database."""
        return MaterialService(mock_db)

    @pytest.fixture
    def mock_section(self) -> MagicMock:
        """Fixture for a mocked CourseSection instance."""
        section = MagicMock(spec=CourseSection)
        section.course_id = 1
        section.section_id = 2
        return section

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        """Fixture for a mocked Course instance."""
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @pytest.fixture
    def mock_author(self) -> MagicMock:
        """Fixture for a mocked User instance representing an author."""
        author = MagicMock(spec=User)
        author.email = "teacher@test.com"
        return author

    @pytest.mark.parametrize(
        "returned_value",
        [
            [MagicMock(spec=CourseMaterial), MagicMock(spec=CourseMaterial)],
            [],
        ],
    )
    def test_get_section_materials(
        self,
        service: MaterialService,
        mock_db: MagicMock,
        mock_section: MagicMock,
        returned_value: list[MagicMock],
    ) -> None:
        """Test that materials for a section are retrieved successfully."""
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = returned_value

        result = service.get_section_materials(mock_section)

        assert result == returned_value
        mock_db.query.assert_called_once_with(CourseMaterial)
        mock_query.filter.assert_called_once()

    @pytest.mark.parametrize(
        ("title", "description"),
        [
            ("Test Material", "Test Description"),
            ("Test Material", ""),
            ("", "Description"),
        ],
    )
    @patch.object(MaterialService.logger, "info")
    def test_create_material(
        self,
        mock_logger: MagicMock,
        service: MaterialService,
        mock_db: MagicMock,
        mock_section: MagicMock,
        mock_author: MagicMock,
        title: str,
        description: str,
    ) -> None:
        """Test that a material is created successfully, and that the correct attributes are set on the CourseMaterial instance."""
        result = service.create_material(
            mock_section,
            title,
            description,
            mock_author,
        )

        assert isinstance(result, CourseMaterial)
        assert result.course_id == mock_section.course_id
        assert result.section_id == mock_section.section_id
        assert result.author == mock_author.email
        assert result.title == title
        assert result.description == description

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @pytest.mark.parametrize(
        ("db_result", "should_raise"),
        [
            (MagicMock(spec=CourseMaterial), False),
            (None, True),
        ],
    )
    @patch.object(MaterialService.logger, "warning")
    def test_get_material(
        self,
        mock_logger: MagicMock,
        service: MaterialService,
        mock_db: MagicMock,
        mock_course: MagicMock,
        db_result: MagicMock | None,
        should_raise: bool,
    ) -> None:
        """Test that a material is retrieved successfully, and that a warning is logged when the material is not found."""
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = db_result

        if should_raise:
            with pytest.raises(material_errors.MaterialNotFoundError) as exc_info:
                service.get_material(mock_course, 999)
            error_text = str(exc_info.value)
            assert "999" in error_text
            assert "1" in error_text
            mock_logger.assert_called_once()
        else:
            result = service.get_material(mock_course, 10)
            assert result == db_result
            mock_db.query.assert_called_once_with(CourseMaterial)
            mock_query.filter.assert_called_once()

    @patch.object(MaterialService.logger, "info")
    def test_delete_material(
        self,
        mock_logger: MagicMock,
        service: MaterialService,
        mock_db: MagicMock,
    ) -> None:
        """Test that a material is deleted successfully."""
        mock_material = MagicMock(spec=CourseMaterial)

        service.delete_material(mock_material)

        mock_db.delete.assert_called_once_with(mock_material)
        mock_logger.assert_called_once()
