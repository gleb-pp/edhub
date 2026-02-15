import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.sections import (
    get_course_sections,
    get_course_feed,
    create_section,
    change_section_order,
    remove_section
)
from src.exceptions import courses as course_errors
from src.exceptions import sections as section_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from datetime import datetime


pytestmark = pytest.mark.asyncio


class TestSectionsRouter:

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.SectionService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_get_course_sections_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()
        mock_sections = [MagicMock(), MagicMock()]

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_course_sections.return_value = mock_sections

        with (
            patch('src.routers.sections.CoursePolicy.assert_course_access') as mock_assert_access,
            patch('src.routers.sections.Section.model_validate') as mock_validate
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_course_sections("course-123", mock_db, "student@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_section_service.get_course_sections.assert_called_once_with(mock_course)
        assert mock_validate.call_count == 2

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_get_course_sections_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_course_sections("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_get_course_sections_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await get_course_sections("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_get_course_sections_participant_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "non-participant@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.sections.CoursePolicy.assert_course_access') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = course_errors.ParticipantRoleRequiredError("non-participant@test.com", "course-123")
            await get_course_sections("course-123", mock_db, "non-participant@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.SectionService')
    @patch('src.routers.sections.MaterialService')
    @patch('src.routers.sections.AssignmentService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_get_course_feed_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_material_service_class,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service
        mock_material_service = MagicMock()
        mock_material_service_class.return_value = mock_material_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_section1 = MagicMock()
        mock_section1.section_id = 1
        mock_section1.title = "Section 1"
        mock_section1.course_id = "course-123"
        mock_section2 = MagicMock()
        mock_section2.section_id = 2
        mock_section2.title = "Section 2"
        mock_section2.course_id = "course-123"

        mock_material1 = MagicMock()
        mock_material1.material_id = 101
        mock_material1.course_id = "course-123"
        mock_material1.section_id = 1
        mock_material1.title = "Material 1"
        mock_material1.creation_time = "2024-01-01"
        mock_material1.author = "teacher@test.com"
        mock_material2 = MagicMock()
        mock_material2.material_id = 102
        mock_material2.course_id = "course-123"
        mock_material2.section_id = 1
        mock_material2.title = "Material 2"
        mock_material2.creation_time = "2024-01-02"
        mock_material2.author = "teacher@test.com"

        mock_assignment1 = MagicMock()
        mock_assignment1.assignment_id = 201
        mock_assignment1.course_id = "course-123"
        mock_assignment1.section_id = 1
        mock_assignment1.title = "Assignment 1"
        mock_assignment1.creation_time = "2024-01-03"
        mock_assignment1.author = "teacher@test.com"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_course_sections.return_value = [mock_section1, mock_section2]

        def get_section_materials_side_effect(section):
            if section.section_id == 1:
                return [mock_material1, mock_material2]
            return []
        mock_material_service.get_section_materials.side_effect = get_section_materials_side_effect

        def get_section_assignments_side_effect(section):
            if section.section_id == 1:
                return [mock_assignment1]
            return []
        mock_assignment_service.get_section_assignments.side_effect = get_section_assignments_side_effect

        with (
            patch('src.routers.sections.CoursePolicy.assert_course_access'),
            patch('src.routers.sections.Section.model_validate') as mock_validate
        ):
            mock_validate.side_effect = lambda x: x
            result = await get_course_feed("course-123", mock_db, "student@test.com")

        assert len(result) == 2
        assert len(result[0].feed) == 3
        assert len(result[1].feed) == 0
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_section_service.get_course_sections.assert_called_once_with(mock_course)
        assert mock_material_service.get_section_materials.call_count == 2
        assert mock_assignment_service.get_section_assignments.call_count == 2

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.SectionService')
    @patch('src.routers.sections.MaterialService')
    @patch('src.routers.sections.AssignmentService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_get_course_feed_sorted_by_creation_time(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_material_service_class,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service
        mock_material_service = MagicMock()
        mock_material_service_class.return_value = mock_material_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_section = MagicMock()
        mock_section.section_id = 1
        mock_section.title = "Section 1"
        mock_section.course_id = "course-123"

        mock_material1 = MagicMock()
        mock_material1.course_id = "course-123"
        mock_material1.section_id = 1
        mock_material1.material_id = 101
        mock_material1.creation_time = datetime(2024, 1, 3)
        mock_material1.author = "teacher@test.com"
        mock_material1.title = "Material 3"
        mock_material2 = MagicMock()
        mock_material2.course_id = "course-123"
        mock_material2.section_id = 1
        mock_material2.material_id = 102
        mock_material2.creation_time = datetime(2024, 1, 1)
        mock_material2.author = "teacher@test.com"
        mock_material2.title = "Material 1"
        mock_assignment1 = MagicMock()
        mock_assignment1.course_id = "course-123"
        mock_assignment1.section_id = 1
        mock_assignment1.assignment_id = 201
        mock_assignment1.creation_time = datetime(2024, 1, 2)
        mock_assignment1.author = "teacher@test.com"
        mock_assignment1.title = "Assignment 1"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_course_sections.return_value = [mock_section]
        mock_material_service.get_section_materials.return_value = [mock_material1, mock_material2]
        mock_assignment_service.get_section_assignments.return_value = [mock_assignment1]

        with (
            patch('src.routers.sections.CoursePolicy.assert_course_access'),
            patch('src.routers.sections.Section.model_validate') as mock_validate
        ):
            mock_validate.side_effect = lambda x: x
            result = await get_course_feed("course-123", mock_db, "student@test.com")

        feed_dates = [post.creation_time for post in result[0].feed]
        assert feed_dates == [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)]

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.SectionService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_create_section_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_section = MagicMock()
        mock_section.section_id = 5

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.create_section.return_value = mock_section

        with (
            patch('src.routers.sections.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            patch('src.routers.sections.SectionID.model_validate') as mock_validate
        ):
            expected_result = {"section_id": 5}
            mock_validate.return_value = expected_result
            result = await create_section("course-123", mock_db, "teacher@test.com", "New Section")

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_section_service.create_section.assert_called_once_with("New Section", mock_course)
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_section)

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.SectionService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_create_section_teacher_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.sections.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123")
            await create_section("course-123", mock_db, "student@test.com", "New Section")

        assert exc_info.value.status_code == 403

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.SectionService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_change_section_order_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.sections.TeacherPolicy.assert_teacher_access') as mock_assert_teacher:
            new_order = [2, 1, 3]
            result = await change_section_order("course-123", mock_db, new_order, "teacher@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_section_service.change_section_order.assert_called_once_with(mock_course, new_order)
        mock_db.commit.assert_called_once()

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.SectionService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_change_section_order_incorrect(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.change_section_order.side_effect = section_errors.IncorrectSectionOrderError()

        with (
            patch('src.routers.sections.TeacherPolicy.assert_teacher_access'),
            pytest.raises(HTTPException) as exc_info
        ):
            await change_section_order("course-123", mock_db, [1], "teacher@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.SectionService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_remove_section_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_section = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.return_value = mock_section

        with patch('src.routers.sections.TeacherPolicy.assert_teacher_access') as mock_assert_teacher:
            result = await remove_section("course-123", 5, mock_db, "teacher@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_section_service.get_section.assert_called_once_with(mock_course, 5)
        mock_section_service.remove_section.assert_called_once_with(mock_section)
        mock_db.commit.assert_called_once()

    @patch('src.routers.sections.UserService')
    @patch('src.routers.sections.CourseService')
    @patch('src.routers.sections.SectionService')
    @patch('src.routers.sections.get_db')
    @patch('src.routers.sections.get_current_user')
    async def test_remove_section_last_section(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_section = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.return_value = mock_section
        mock_section_service.remove_section.side_effect = section_errors.LastSectionDeleteError(5, "course-123")

        with (
            patch('src.routers.sections.TeacherPolicy.assert_teacher_access'),
            pytest.raises(HTTPException) as exc_info
        ):
            await remove_section("course-123", 5, mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 409
