import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.materials import create_material, remove_material, get_material
from src.exceptions import courses as course_errors
from src.exceptions import materials as material_errors
from src.exceptions import sections as section_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success


pytestmark = pytest.mark.asyncio


class TestMaterialsRouter:

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.SectionService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_create_material_success_as_teacher(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
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
        mock_material_service = MagicMock()
        mock_material_service_class.return_value = mock_material_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_course.course_id = "course-123"
        mock_section = MagicMock()
        mock_section.section_id = 1
        mock_material = MagicMock()
        mock_material.course_id = "course-123"
        mock_material.material_id = 42
        mock_material.section_id = 1

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.return_value = mock_section
        mock_material_service.create_material.return_value = mock_material

        with (
            patch('src.routers.materials.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            patch('src.routers.materials.MaterialID.model_validate') as mock_validate
        ):
            expected_result = {"course_id": "course-123", "material_id": 42, "section_id": 1}
            mock_validate.return_value = expected_result
            result = await create_material(
                "course-123", 1, mock_db, "Test Material", "Test Description", "teacher@test.com"
            )

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_section_service.get_section.assert_called_once_with(mock_course, 1)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_material_service.create_material.assert_called_once_with(
            mock_section, "Test Material", "Test Description", mock_teacher
        )
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_material)

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.SectionService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_create_material_success_as_admin(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service
        mock_material_service = MagicMock()
        mock_material_service_class.return_value = mock_material_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = True
        mock_course = MagicMock()
        mock_course.course_id = "course-123"
        mock_section = MagicMock()
        mock_section.section_id = 1
        mock_material = MagicMock()
        mock_material.course_id = "course-123"
        mock_material.material_id = 42
        mock_material.section_id = 1

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.return_value = mock_section
        mock_material_service.create_material.return_value = mock_material

        with patch('src.routers.materials.MaterialID.model_validate') as mock_validate:
            expected_result = {"course_id": "course-123", "material_id": 42, "section_id": 1}
            mock_validate.return_value = expected_result
            result = await create_material(
                "course-123", 1, mock_db, "Test Material", "Test Description", "admin@test.com"
            )

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("admin@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_section_service.get_section.assert_called_once_with(mock_course, 1)
        mock_material_service.create_material.assert_called_once_with(
            mock_section, "Test Material", "Test Description", mock_teacher
        )
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_material)

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_create_material_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("teacher@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await create_material(
                "course-123", 1, mock_db, "Test Material", "Test Description", "teacher@test.com"
            )

        assert exc_info.value.status_code == 401

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_create_material_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
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

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await create_material(
                "course-123", 1, mock_db, "Test Material", "Test Description", "teacher@test.com"
            )

        assert exc_info.value.status_code == 400

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.SectionService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_create_material_section_not_found(
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
        mock_section_service.get_section.side_effect = section_errors.SectionNotFoundError(1, "course-123")

        with pytest.raises(HTTPException) as exc_info:
            await create_material(
                "course-123", 1, mock_db, "Test Material", "Test Description", "teacher@test.com"
            )

        assert exc_info.value.status_code == 400

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.SectionService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_create_material_teacher_role_required(
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

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.materials.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123")
            await create_material(
                "course-123", 1, mock_db, "Test Material", "Test Description", "student@test.com"
            )

        assert exc_info.value.status_code == 403

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_remove_material_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
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
        mock_material_service = MagicMock()
        mock_material_service_class.return_value = mock_material_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_material = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_material_service.get_material.return_value = mock_material

        with patch('src.routers.materials.TeacherPolicy.assert_teacher_access') as mock_assert_teacher:
            result = await remove_material("course-123", 10, mock_db, "teacher@test.com")

        assert isinstance(result, Success)
        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_material_service.get_material.assert_called_once_with(mock_course, 10)
        mock_material_service.delete_material.assert_called_once_with(mock_material)
        mock_db.commit.assert_called_once()

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_remove_material_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
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
        mock_material_service = MagicMock()
        mock_material_service_class.return_value = mock_material_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_material_service.get_material.side_effect = material_errors.MaterialNotFoundError("course-123", 999)

        with (
            patch('src.routers.materials.TeacherPolicy.assert_teacher_access'),
            pytest.raises(HTTPException) as exc_info
        ):
            await remove_material("course-123", 999, mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_remove_material_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
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

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await remove_material("course-123", 10, mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_remove_material_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("teacher@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await remove_material("course-123", 10, mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_remove_material_teacher_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
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
            patch('src.routers.materials.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123")
            await remove_material("course-123", 10, mock_db, "student@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_get_material_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
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
        mock_material_service = MagicMock()
        mock_material_service_class.return_value = mock_material_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()
        mock_material = MagicMock()
        mock_material.course_id = "course-123"
        mock_material.material_id = 10
        mock_material.title = "Test Material"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_material_service.get_material.return_value = mock_material

        with (
            patch('src.routers.materials.CoursePolicy.assert_course_access') as mock_assert_access,
            patch('src.routers.materials.Material.model_validate') as mock_validate
        ):
            expected_result = {"course_id": "course-123", "material_id": 10, "title": "Test Material"}
            mock_validate.return_value = expected_result
            result = await get_material("course-123", 10, mock_db, "student@test.com")

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_material_service.get_material.assert_called_once_with(mock_course, 10)
        mock_validate.assert_called_once_with(mock_material)

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_get_material_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_material("course-123", 10, mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_get_material_course_not_found(
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
            await get_material("course-123", 10, mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_get_material_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
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
        mock_material_service = MagicMock()
        mock_material_service_class.return_value = mock_material_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_material_service.get_material.side_effect = material_errors.MaterialNotFoundError("course-123", 999)

        with (
            patch('src.routers.materials.CoursePolicy.assert_course_access'),
            pytest.raises(HTTPException) as exc_info
        ):
            await get_material("course-123", 999, mock_db, "user@test.com")

        assert exc_info.value.status_code == 404

    @patch('src.routers.materials.UserService')
    @patch('src.routers.materials.CourseService')
    @patch('src.routers.materials.MaterialService')
    @patch('src.routers.materials.get_db')
    @patch('src.routers.materials.get_current_user')
    async def test_get_material_participant_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_material_service_class,
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
            patch('src.routers.materials.CoursePolicy.assert_course_access') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = course_errors.ParticipantRoleRequiredError("non-participant@test.com", "course-123")
            await get_material("course-123", 10, mock_db, "non-participant@test.com")

        assert exc_info.value.status_code == 403
