from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.materials as material_errors
from src.services import MaterialService
from src.repo import Course, CourseMaterial, CourseSection, User


class TestMaterialService:

    def test_get_section_materials_success(self):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_section.course_id = 1
        mock_section.section_id = 2
        
        mock_query = mock_db.query.return_value
        expected_materials = [MagicMock(spec=CourseMaterial), MagicMock(spec=CourseMaterial)]
        mock_query.filter.return_value.all.return_value = expected_materials
        
        service = MaterialService(mock_db)
        result = service.get_section_materials(mock_section)
        
        assert result == expected_materials
        mock_db.query.assert_called_once_with(CourseMaterial)
        mock_query.filter.assert_called_once()

    def test_get_section_materials_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_section.course_id = 1
        mock_section.section_id = 2
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.all.return_value = []
        
        service = MaterialService(mock_db)
        result = service.get_section_materials(mock_section)
        
        assert result == []

    @patch.object(MaterialService.logger, 'info')
    def test_create_material_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_section.course_id = 1
        mock_section.section_id = 2
        mock_author = MagicMock(spec=User)
        mock_author.email = "teacher@test.com"
        
        service = MaterialService(mock_db)
        result = service.create_material(mock_section, "Test Material", "Test Description", mock_author)
        
        assert isinstance(result, CourseMaterial)
        assert result.course_id == mock_section.course_id
        assert result.section_id == mock_section.section_id
        assert result.author == mock_author.email
        assert result.title == "Test Material"
        assert result.description == "Test Description"
        
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    @patch.object(MaterialService.logger, 'info')
    def test_create_material_without_description(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_section.course_id = 1
        mock_section.section_id = 2
        mock_author = MagicMock(spec=User)
        mock_author.email = "teacher@test.com"
        
        service = MaterialService(mock_db)
        result = service.create_material(mock_section, "Test Material", "", mock_author)
        
        assert result.description == ""

    def test_create_material_empty_title(self):
        mock_db = MagicMock(spec=Session)
        mock_section = MagicMock(spec=CourseSection)
        mock_author = MagicMock(spec=User)
        
        service = MaterialService(mock_db)
        result = service.create_material(mock_section, "", "Description", mock_author)
        
        assert result.title == ""

    def test_get_material_success(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        expected_material = MagicMock(spec=CourseMaterial)
        mock_query.filter.return_value.first.return_value = expected_material
        
        service = MaterialService(mock_db)
        result = service.get_material(mock_course, 10)
        
        assert result == expected_material
        mock_db.query.assert_called_once_with(CourseMaterial)
        mock_query.filter.assert_called_once()

    @patch.object(MaterialService.logger, 'warning')
    def test_get_material_not_found(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        service = MaterialService(mock_db)
        
        with pytest.raises(material_errors.MaterialNotFoundError) as exc_info:
            service.get_material(mock_course, 999)
        
        assert "999" in str(exc_info.value)
        assert "1" in str(exc_info.value)
        mock_logger.assert_called_once()

    @patch.object(MaterialService.logger, 'info')
    def test_delete_material_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_material = MagicMock(spec=CourseMaterial)
        mock_material.material_id = 10
        mock_material.course_id = 1
        
        service = MaterialService(mock_db)
        service.delete_material(mock_material)
        
        mock_db.delete.assert_called_once_with(mock_material)
        mock_logger.assert_called_once()
