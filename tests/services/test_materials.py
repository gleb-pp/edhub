from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.materials as material_errors
from src.repo import Course, CourseMaterial, CourseSection, User
from src.services import MaterialService


class TestMaterialService:

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db) -> MaterialService:
        return MaterialService(mock_db)

    @pytest.fixture
    def mock_section(self) -> MagicMock:
        section = MagicMock(spec=CourseSection)
        section.course_id = 1
        section.section_id = 2
        return section

    @pytest.fixture
    def mock_course(self) -> MagicMock:
        course = MagicMock(spec=Course)
        course.course_id = 1
        return course

    @pytest.fixture
    def mock_author(self) -> MagicMock:
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
    def test_get_section_materials(self, service, mock_db, mock_section, returned_value) -> None:
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = returned_value

        result = service.get_section_materials(mock_section)

        assert result == returned_value
        mock_db.query.assert_called_once_with(CourseMaterial)
        mock_query.filter.assert_called_once()

    @pytest.mark.parametrize(
        "title, description",
        [
            ("Test Material", "Test Description"),
            ("Test Material", ""),
            ("", "Description"),
        ],
    )
    @patch.object(MaterialService.logger, "info")
    def test_create_material(
        self,
        mock_logger,
        service,
        mock_db,
        mock_section,
        mock_author,
        title,
        description,
    ) -> None:
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
        "db_result, should_raise",
        [
            (MagicMock(spec=CourseMaterial), False),
            (None, True),
        ],
    )
    @patch.object(MaterialService.logger, "warning")
    def test_get_material(
        self,
        mock_logger,
        service,
        mock_db,
        mock_course,
        db_result,
        should_raise,
    ) -> None:
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
    def test_delete_material(self, mock_logger, service, mock_db) -> None:
        mock_material = MagicMock(spec=CourseMaterial)

        service.delete_material(mock_material)

        mock_db.delete.assert_called_once_with(mock_material)
        mock_logger.assert_called_once()
