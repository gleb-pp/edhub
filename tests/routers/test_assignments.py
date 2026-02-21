from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import assignments as assignment_errors
from src.exceptions import courses as course_errors
from src.exceptions import sections as section_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.routers.assignments import (
    create_assignment,
    get_assignment,
    get_course_assignments,
    remove_assignment,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db() -> MagicMock:
    """Mock for the database session."""
    return MagicMock()


@pytest.fixture
def mock_user_service() -> Generator[MagicMock, None, None]:
    """Mock for the UserService class."""
    with patch("src.routers.assignments.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service() -> Generator[MagicMock, None, None]:
    """Mock for the CourseService class."""
    with patch("src.routers.assignments.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_section_service() -> Generator[MagicMock, None, None]:
    """Mock for the SectionService class."""
    with patch("src.routers.assignments.SectionService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_assignment_service() -> Generator[MagicMock, None, None]:
    """Mock for the AssignmentService class."""
    with patch("src.routers.assignments.AssignmentService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user() -> Generator[MagicMock, None, None]:
    """Mock for the get_current_user dependency."""
    with patch("src.routers.assignments.get_current_user") as mock_func:
        yield mock_func


@pytest.fixture
def mock_user() -> MagicMock:
    """Mock user object with default properties."""
    user = MagicMock()
    user.is_admin = False
    user.email = "user@test.com"
    return user


@pytest.fixture
def mock_course() -> MagicMock:
    """Mock course object with default properties."""
    course = MagicMock()
    course.course_id = "course-123"
    return course


@pytest.fixture
def mock_section() -> MagicMock:
    """Mock section object with default properties."""
    section = MagicMock()
    section.section_id = 1
    section.course_id = "course-123"
    return section


@pytest.fixture
def mock_assignment() -> MagicMock:
    """Mock assignment object with default properties."""
    assignment = MagicMock()
    assignment.course_id = "course-123"
    assignment.assignment_id = 10
    assignment.section_id = 1
    assignment.title = "Test Assignment"
    assignment.description = "Test Description"
    return assignment


class TestAssignmentsRouter:
    """Test suite for the assignments router."""

    @pytest.mark.parametrize(
        ("user_email", "is_admin", "policy_check"),
        [
            ("teacher@test.com", False, True),
            ("admin@test.com", True, False),
        ],
        ids=["as_teacher", "as_admin"],
    )
    async def test_create_assignment_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_section_service: MagicMock,
        mock_assignment_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        mock_section: MagicMock,
        mock_assignment: MagicMock,
        user_email: str,
        is_admin: bool,
        policy_check: bool,
    ) -> None:
        """Test the successful creation of an assignment by both a teacher and an admin."""
        mock_get_current_user.return_value = user_email
        mock_user.is_admin = is_admin
        mock_user.email = user_email

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.return_value = mock_section
        mock_assignment_service.create_assignment.return_value = mock_assignment

        expected_result = {
            "course_id": mock_course.course_id,
            "assignment_id": mock_assignment.assignment_id,
            "section_id": mock_section.section_id,
        }

        with patch("src.routers.assignments.AssignmentID.model_validate") as mock_validate:
            mock_validate.return_value = expected_result
            if policy_check:
                with patch("src.routers.assignments.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
                    result = await create_assignment(
                        mock_course.course_id,
                        mock_section.section_id,
                        mock_db,
                        "Test Title",
                        "Test Description",
                        user_email,
                    )
                    mock_assert_teacher.assert_called_once_with(mock_user, mock_course, mock_db)
            else:
                result = await create_assignment(
                    mock_course.course_id,
                    mock_section.section_id,
                    mock_db,
                    "Test Title",
                    "Test Description",
                    user_email,
                )

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with(user_email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_section_service.get_section.assert_called_once_with(mock_course, mock_section.section_id)
        mock_assignment_service.create_assignment.assert_called_once_with(
            mock_section, "Test Title", "Test Description", mock_user,
        )
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_assignment)

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
    async def test_create_assignment_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_section_service: MagicMock,
        mock_assignment_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
    ) -> None:
        """Test error scenarios for creating an assignment."""
        mock_get_current_user.return_value = "teacher@test.com"
        mock_user.is_admin = False
        mock_user.email = "teacher@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "section_not_found":
            mock_section_service.get_section.side_effect = side_effect
        else:
            mock_section_service.get_section.return_value = MagicMock()

        if error_scenario == "teacher_role_required":
            patcher = patch("src.routers.assignments.TeacherPolicy.assert_teacher_access")
            mock_assert_teacher = patcher.start()
            mock_assert_teacher.side_effect = side_effect
        else:
            patcher = None

        try:
            with pytest.raises(HTTPException) as exc_info:
                await create_assignment(
                    mock_course.course_id,
                    1,
                    mock_db,
                    "Test Title",
                    "Test Description",
                    "teacher@test.com",
                )
        finally:
            if patcher:
                patcher.stop()

        assert exc_info.value.status_code == expected_status
        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status"),
        [
            ("user_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400),
            ("assignment_not_found", assignment_errors.AssignmentNotFoundError("course-123", 999), 400),
        ],
        ids=["user_not_found", "course_not_found", "assignment_not_found"],
    )
    async def test_remove_assignment_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_assignment_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
    ) -> None:
        """Test error scenarios for removing an assignment."""
        mock_get_current_user.return_value = "teacher@test.com"
        mock_user.is_admin = False
        mock_user.email = "teacher@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "assignment_not_found":
            mock_assignment_service.get_assignment.side_effect = side_effect

        with (
            patch("src.routers.assignments.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info,
        ):
            await remove_assignment(mock_course.course_id, 999, mock_db, "teacher@test.com")

        assert exc_info.value.status_code == expected_status
        if error_scenario == "assignment_not_found":
            mock_assert_teacher.assert_called_once()
        mock_db.commit.assert_not_called()

    async def test_remove_assignment_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_assignment_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        mock_assignment: MagicMock,
    ) -> None:
        """Test the successful removal of an assignment."""
        mock_get_current_user.return_value = "teacher@test.com"
        mock_user.is_admin = False
        mock_user.email = "teacher@test.com"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment

        with patch("src.routers.assignments.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
            result = await remove_assignment(mock_course.course_id, 10, mock_db, "teacher@test.com")

        assert isinstance(result, Success)
        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_teacher.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, 10)
        mock_assignment_service.delete_assignment.assert_called_once_with(mock_assignment)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status"),
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400),
            ("assignment_not_found", assignment_errors.AssignmentNotFoundError("course-123", 999), 404),
            ("participant_role_required", course_errors.ParticipantRoleRequiredError("user@test.com", "course-123"), 403),
        ],
        ids=["user_not_found", "course_not_found", "assignment_not_found", "participant_role_required"],
    )
    async def test_get_assignment_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_assignment_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
    ) -> None:
        """Test error scenarios for getting an assignment."""
        mock_get_current_user.return_value = "user@test.com"
        mock_user.is_admin = False
        mock_user.email = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "assignment_not_found":
            mock_assignment_service.get_assignment.side_effect = side_effect

        if error_scenario == "participant_role_required":
            patcher = patch("src.routers.assignments.CoursePolicy.assert_course_access")
            mock_assert_access = patcher.start()
            mock_assert_access.side_effect = side_effect
        else:
            patcher = None

        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_assignment(
                    mock_course.course_id,
                    10,
                    mock_db,
                    "user@test.com",
                )
        finally:
            if patcher:
                patcher.stop()

        assert exc_info.value.status_code == expected_status

    async def test_get_assignment_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_assignment_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        mock_assignment: MagicMock,
    ) -> None:
        """Test the successful retrieval of an assignment."""
        mock_get_current_user.return_value = "user@test.com"
        mock_user.is_admin = False
        mock_user.email = "user@test.com"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment

        expected_result = {
            "course_id": mock_course.course_id,
            "assignment_id": mock_assignment.assignment_id,
            "title": mock_assignment.title,
        }

        with (
            patch("src.routers.assignments.CoursePolicy.assert_course_access") as mock_assert_access,
            patch("src.routers.assignments.Assignment.model_validate") as mock_validate,
        ):
            mock_validate.return_value = expected_result
            result = await get_assignment(mock_course.course_id, 10, mock_db, "user@test.com")

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, 10)
        mock_validate.assert_called_once_with(mock_assignment)

    @pytest.mark.parametrize(
        ("assignments_list", "expected_count"),
        [
            ([MagicMock(), MagicMock()], 2),
            ([], 0),
        ],
        ids=["with_assignments", "empty"],
    )
    async def test_get_course_assignments(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_assignment_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        assignments_list: list[MagicMock],
        expected_count: int,
    ) -> None:
        """Test the successful retrieval of course assignments for both cases when there are assignments and when there are none."""
        mock_get_current_user.return_value = "student@test.com"
        mock_user.is_admin = False
        mock_user.email = "student@test.com"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_course_assignments.return_value = assignments_list

        with (
            patch("src.routers.assignments.CoursePolicy.assert_course_access"),
            patch("src.routers.assignments.Assignment.model_validate") as mock_validate,
        ):
            mock_validate.side_effect = lambda x: {"course_id": x.course_id if hasattr(x, "course_id") else "course-123"}
            result = await get_course_assignments(mock_course.course_id, mock_db, "student@test.com")

        assert len(result) == expected_count
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assignment_service.get_course_assignments.assert_called_once_with(mock_course)
        assert mock_validate.call_count == expected_count

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status"),
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400),
            ("participant_role_required", course_errors.ParticipantRoleRequiredError("user@test.com", "course-123"), 403),
        ],
        ids=["user_not_found", "course_not_found", "participant_role_required"],
    )
    async def test_get_course_assignments_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
    ) -> None:
        """Test error scenarios for getting course assignments."""
        mock_get_current_user.return_value = "user@test.com"
        mock_user.is_admin = False
        mock_user.email = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "participant_role_required":
            patcher = patch("src.routers.assignments.CoursePolicy.assert_course_access")
            mock_assert_access = patcher.start()
            mock_assert_access.side_effect = side_effect
        else:
            patcher = None

        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_course_assignments(
                    mock_course.course_id,
                    mock_db,
                    "user@test.com",
                )
        finally:
            if patcher:
                patcher.stop()

        assert exc_info.value.status_code == expected_status
