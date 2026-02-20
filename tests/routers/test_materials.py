from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import courses as course_errors
from src.exceptions import materials as material_errors
from src.exceptions import sections as section_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.routers.materials import create_material, get_material, remove_material

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db() -> MagicMock:
    """Mock for the database session."""
    return MagicMock()


@pytest.fixture
def mock_user_service() -> Generator[MagicMock, None, None]:
    """Mock for the UserService class."""
    with patch("src.routers.materials.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service() -> Generator[MagicMock, None, None]:
    """Mock for the CourseService class."""
    with patch("src.routers.materials.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_section_service() -> Generator[MagicMock, None, None]:
    """Mock for the SectionService class."""
    with patch("src.routers.materials.SectionService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_material_service() -> Generator[MagicMock, None, None]:
    """Mock for the MaterialService class."""
    with patch("src.routers.materials.MaterialService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user() -> Generator[MagicMock, None, None]:
    """Mock for the get_current_user dependency."""
    with patch("src.routers.materials.get_current_user") as mock_func:
        yield mock_func


@pytest.fixture
def mock_teacher() -> MagicMock:
    """Mock for a teacher user."""
    teacher = MagicMock()
    teacher.isadmin = False
    teacher.email = "teacher@test.com"
    return teacher


@pytest.fixture
def mock_user() -> MagicMock:
    """Mock for a regular user."""
    user = MagicMock()
    user.isadmin = False
    user.email = "user@test.com"
    return user


@pytest.fixture
def mock_course() -> MagicMock:
    """Mock for a course object."""
    course = MagicMock()
    course.course_id = "course-123"
    return course


@pytest.fixture
def mock_section() -> MagicMock:
    """Mock for a section object."""
    section = MagicMock()
    section.section_id = 1
    return section


@pytest.fixture
def mock_material() -> MagicMock:
    """Mock for a material object."""
    material = MagicMock()
    material.course_id = "course-123"
    material.material_id = 42
    material.section_id = 1
    material.title = "Test Material"
    return material


class TestMaterialsRouter:
    """Test suite for the materials router."""

    @pytest.mark.parametrize(
        ("user_email", "is_admin", "should_check_teacher"),
        [
            ("teacher@test.com", False, True),
            ("admin@test.com", True, False),
        ],
        ids=["as_teacher", "as_admin"],
    )
    async def test_create_material_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_section_service: MagicMock,
        mock_material_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
        mock_section: MagicMock,
        mock_material: MagicMock,
        user_email: str,
        is_admin: bool,
        should_check_teacher: bool,
    ) -> None:
        """Test successful creation of a material."""
        mock_get_current_user.return_value = user_email
        mock_teacher.isadmin = is_admin
        mock_teacher.email = user_email

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.return_value = mock_section
        mock_material_service.create_material.return_value = mock_material

        expected_result = {
            "course_id": mock_course.course_id,
            "material_id": mock_material.material_id,
            "section_id": mock_section.section_id,
        }

        with patch("src.routers.materials.MaterialID.model_validate") as mock_validate:
            mock_validate.return_value = expected_result

            if should_check_teacher:
                with patch("src.routers.materials.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
                    result = await create_material(
                        mock_course.course_id,
                        mock_section.section_id,
                        mock_db,
                        "Test Material",
                        "Test Description",
                        user_email,
                    )
                    mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
            else:
                with patch("src.routers.materials.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
                    result = await create_material(
                        mock_course.course_id,
                        mock_section.section_id,
                        mock_db,
                        "Test Material",
                        "Test Description",
                        user_email,
                    )
                    mock_assert_teacher.assert_not_called()

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with(user_email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_section_service.get_section.assert_called_once_with(mock_course, mock_section.section_id)
        mock_material_service.create_material.assert_called_once_with(
            mock_section, "Test Material", "Test Description", mock_teacher,
        )
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_material)

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status"),
        [
            ("user_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400),
            ("section_not_found", section_errors.SectionNotFoundError(1, "course-123"), 400),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403),
        ],
        ids=["user_not_found", "course_not_found", "section_not_found", "teacher_role_required"],
    )
    async def test_create_material_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_section_service: MagicMock,
        mock_material_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
    ) -> None:
        """Test error scenarios for creating a material."""
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_teacher

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "section_not_found":
            mock_section_service.get_section.side_effect = side_effect
        else:
            mock_section_service.get_section.return_value = MagicMock()

        if error_scenario == "teacher_role_required":
            patcher = patch("src.routers.materials.TeacherPolicy.assert_teacher_access")
            mock_assert = patcher.start()
            mock_assert.side_effect = side_effect
        else:
            patcher = None

        try:
            with pytest.raises(HTTPException) as exc_info:
                await create_material(
                    mock_course.course_id,
                    1,
                    mock_db,
                    "Test Material",
                    "Test Description",
                    "teacher@test.com",
                )
        finally:
            if patcher:
                patcher.stop()

        assert exc_info.value.status_code == expected_status
        mock_material_service.create_material.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status", "should_check_teacher"),
        [
            ("user_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("material_not_found", material_errors.MaterialNotFoundError("course-123", 999), 400, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "course_not_found", "material_not_found", "teacher_role_required"],
    )
    async def test_remove_material_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_material_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
        should_check_teacher: bool,
    ) -> None:
        """Test error scenarios for removing a material."""
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_teacher

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "material_not_found":
            mock_material_service.get_material.side_effect = side_effect

        with patch("src.routers.materials.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
            if error_scenario == "teacher_role_required":
                mock_assert_teacher.side_effect = side_effect
            with pytest.raises(HTTPException) as exc_info:
                await remove_material(mock_course.course_id, 999, mock_db, "teacher@test.com")

            assert exc_info.value.status_code == expected_status

            if should_check_teacher:
                if error_scenario == "teacher_role_required":
                    mock_assert_teacher.assert_called_once()
                else:
                    mock_assert_teacher.assert_called_once()
            else:
                mock_assert_teacher.assert_not_called()

        mock_material_service.delete_material.assert_not_called()
        mock_db.commit.assert_not_called()

    async def test_remove_material_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_material_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
        mock_material: MagicMock,
    ) -> None:
        """Test successful removal of a material."""
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_material_service.get_material.return_value = mock_material

        with patch("src.routers.materials.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
            result = await remove_material(mock_course.course_id, 42, mock_db, "teacher@test.com")

        assert isinstance(result, Success)
        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_material_service.get_material.assert_called_once_with(mock_course, 42)
        mock_material_service.delete_material.assert_called_once_with(mock_material)
        mock_db.commit.assert_called_once()

    async def test_get_material_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_material_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        mock_material: MagicMock,
    ) -> None:
        """Test successful retrieval of a material."""
        mock_get_current_user.return_value = "user@test.com"
        mock_user.isadmin = False

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_material_service.get_material.return_value = mock_material

        expected_result = {
            "course_id": mock_course.course_id,
            "material_id": mock_material.material_id,
            "title": mock_material.title,
        }

        with (
            patch("src.routers.materials.CoursePolicy.assert_course_access") as mock_assert_access,
            patch("src.routers.materials.Material.model_validate") as mock_validate,
        ):
            mock_validate.return_value = expected_result
            result = await get_material(mock_course.course_id, 42, mock_db, "user@test.com")

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_material_service.get_material.assert_called_once_with(mock_course, 42)
        mock_validate.assert_called_once_with(mock_material)

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status", "should_check_access"),
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("material_not_found", material_errors.MaterialNotFoundError("course-123", 999), 404, True),
            ("participant_role_required", course_errors.ParticipantRoleRequiredError("user@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "course_not_found", "material_not_found", "participant_role_required"],
    )
    async def test_get_material_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_material_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
        should_check_access: bool,
    ) -> None:
        """Test error scenarios for retrieving a material."""
        mock_get_current_user.return_value = "user@test.com"
        mock_user.isadmin = False

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "material_not_found":
            mock_material_service.get_material.side_effect = side_effect

        with patch("src.routers.materials.CoursePolicy.assert_course_access") as mock_assert_access:
            if error_scenario == "participant_role_required":
                mock_assert_access.side_effect = side_effect
            with pytest.raises(HTTPException) as exc_info:
                await get_material(mock_course.course_id, 999, mock_db, "user@test.com")

            assert exc_info.value.status_code == expected_status

            if should_check_access:
                if error_scenario == "participant_role_required":
                    mock_assert_access.assert_called_once()
                else:
                    mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

        with patch("src.routers.materials.Material.model_validate") as mock_validate:
            mock_validate.assert_not_called()
