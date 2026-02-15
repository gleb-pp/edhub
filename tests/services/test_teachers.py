from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.services.teachers import TeacherService
from src.repo.courses import Course
from src.repo.teachers import Teaches
from src.repo.users import User


class TestTeacherService:

    def test_get_course_teachers_success(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        expected_teachers = [MagicMock(spec=User), MagicMock(spec=User)]
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = expected_teachers
        
        service = TeacherService(mock_db)
        result = service.get_course_teachers(mock_course)
        
        assert result == expected_teachers
        mock_db.query.assert_called_once_with(User)
        mock_query.join.assert_called_once()

    def test_get_course_teachers_empty(self):
        mock_db = MagicMock(spec=Session)
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        mock_join = mock_query.join.return_value
        mock_filter = mock_join.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = []
        
        service = TeacherService(mock_db)
        result = service.get_course_teachers(mock_course)
        
        assert result == []

    @patch.object(TeacherService.logger, 'info')
    def test_invite_teacher_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_teacher = MagicMock(spec=User)
        mock_teacher.email = "teacher@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        service = TeacherService(mock_db)
        service.invite_teacher(mock_teacher, mock_course)
        
        mock_db.add.assert_called_once()
        added_teaches = mock_db.add.call_args[0][0]
        assert isinstance(added_teaches, Teaches)
        assert added_teaches.email == mock_teacher.email
        assert added_teaches.course_id == mock_course.course_id
        mock_logger.assert_called_once()

    @patch.object(TeacherService.logger, 'info')
    def test_remove_teacher_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_teacher = MagicMock(spec=User)
        mock_teacher.email = "teacher@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_teaches = MagicMock(spec=Teaches)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_teaches
        
        service = TeacherService(mock_db)
        service.remove_teacher(mock_teacher, mock_course)
        
        mock_db.query.assert_called_once_with(Teaches)
        mock_query.filter.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_teaches)
        mock_logger.assert_called_once()

    @patch.object(TeacherService.logger, 'info')
    def test_remove_teacher_not_found_does_nothing(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_teacher = MagicMock(spec=User)
        mock_teacher.email = "teacher@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None
        
        service = TeacherService(mock_db)
        service.remove_teacher(mock_teacher, mock_course)
        
        mock_db.query.assert_called_once_with(Teaches)
        mock_query.filter.assert_called_once()
        mock_db.delete.assert_not_called()
        mock_logger.assert_not_called()

    @patch.object(TeacherService.logger, 'info')
    def test_change_course_instructor_success(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_instructor = MagicMock(spec=User)
        mock_instructor.email = "old_instructor@test.com"
        mock_teacher = MagicMock(spec=User)
        mock_teacher.email = "new_instructor@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_course.instructor = mock_instructor.email
        
        mock_teaches = MagicMock(spec=Teaches)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_teaches
        
        service = TeacherService(mock_db)
        service.change_course_instructor(mock_instructor, mock_teacher, mock_course)
        
        assert mock_course.instructor == mock_teacher.email
        mock_db.delete.assert_called_once_with(mock_teaches)
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        assert mock_logger.call_count == 3

    @patch.object(TeacherService.logger, 'info')
    def test_change_course_instructor_same_person(self, mock_logger):
        mock_db = MagicMock(spec=Session)
        mock_instructor = MagicMock(spec=User)
        mock_instructor.email = "teacher@test.com"
        mock_teacher = MagicMock(spec=User)
        mock_teacher.email = "teacher@test.com"
        mock_course = MagicMock(spec=Course)
        mock_course.course_id = 1
        mock_course.instructor = "old_instructor@test.com"
        
        mock_teaches = MagicMock(spec=Teaches)
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_teaches
        
        service = TeacherService(mock_db)
        service.change_course_instructor(mock_instructor, mock_teacher, mock_course)
        
        assert mock_course.instructor == mock_teacher.email
        mock_db.delete.assert_called_once_with(mock_teaches)
        mock_db.add.assert_called_once()
        added_teaches = mock_db.add.call_args[0][0]
        assert isinstance(added_teaches, Teaches)
        assert added_teaches.email == mock_instructor.email
        assert added_teaches.course_id == mock_course.course_id
        mock_db.flush.assert_called_once()
        assert mock_logger.call_count == 3
