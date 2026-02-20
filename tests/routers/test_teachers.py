from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import courses as course_errors
from src.exceptions import parents as parent_errors
from src.exceptions import students as student_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.routers.teachers import (
    change_course_instructor,
    get_course_teachers,
    invite_teacher,
    remove_teacher,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db() -> MagicMock:
    """Fixture for mocking the database session."""
    return MagicMock()


@pytest.fixture
def mock_user_service() -> Generator[MagicMock, None, None]:
    """Fixture for mocking the UserService."""
    with patch("src.routers.teachers.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service() -> Generator[MagicMock, None, None]:
    """Fixture for mocking the CourseService."""
    with patch("src.routers.teachers.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_teacher_service() -> Generator[MagicMock, None, None]:
    """Fixture for mocking the TeacherService."""
    with patch("src.routers.teachers.TeacherService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_personalization_service() -> Generator[MagicMock, None, None]:
    """Fixture for mocking the PersonalizationService."""
    with patch("src.routers.teachers.PersonalizationService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user() -> Generator[MagicMock, None, None]:
    """Fixture for mocking the get_current_user dependency."""
    with patch("src.routers.teachers.get_current_user") as mock_func:
        yield mock_func


@pytest.fixture
def mock_user() -> MagicMock:
    """Fixture for a mock user object."""
    user = MagicMock()
    user.is_admin = False
    user.email = "user@test.com"
    return user


@pytest.fixture
def mock_instructor() -> MagicMock:
    """Fixture for a mock instructor user object."""
    instructor = MagicMock()
    instructor.is_admin = False
    instructor.email = "instructor@test.com"
    return instructor


@pytest.fixture
def mock_teacher() -> MagicMock:
    """Fixture for a mock teacher user object."""
    teacher = MagicMock()
    teacher.is_admin = False
    teacher.email = "teacher@test.com"
    return teacher


@pytest.fixture
def mock_course() -> MagicMock:
    """Fixture for a mock course object."""
    course = MagicMock()
    course.course_id = "course-123"
    course.instructor = "instructor@test.com"
    return course


class TestTeachersRouter:
    """Test suite for the teachers router."""

    async def test_get_course_teachers_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_teacher_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
    ) -> None:
        """Test the successful retrieval of course teachers."""
        mock_get_current_user.return_value = "user@test.com"
        mock_user.is_admin = False
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        mock_teachers = [MagicMock(), MagicMock()]
        mock_teacher_service.get_course_teachers.return_value = mock_teachers

        with (
            patch("src.routers.teachers.CoursePolicy.assert_course_access") as mock_assert_access,
            patch("src.routers.teachers.User.model_validate") as mock_validate,
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_course_teachers(mock_course.course_id, mock_db, "user@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_teacher_service.get_course_teachers.assert_called_once_with(mock_course)
        assert mock_validate.call_count == 2

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status", "should_check_policy"),
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("participant_role_required", course_errors.ParticipantRoleRequiredError("user@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "course_not_found", "participant_role_required"],
    )
    async def test_get_course_teachers_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_teacher_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_user: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
        should_check_policy: bool,
    ) -> None:
        """Test error scenarios for retrieving course teachers."""
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with patch("src.routers.teachers.CoursePolicy.assert_course_access") as mock_assert_access:
            if error_scenario == "participant_role_required":
                mock_assert_access.side_effect = side_effect
            with pytest.raises(HTTPException) as exc_info:
                await get_course_teachers(mock_course.course_id, mock_db, "user@test.com")

            assert exc_info.value.status_code == expected_status

            if should_check_policy:
                mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

        with patch("src.routers.teachers.User.model_validate") as mock_validate:
            mock_validate.assert_not_called()

    async def test_invite_teacher_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_teacher_service: MagicMock,
        mock_personalization_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_instructor: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
    ) -> None:
        """Test the successful invitation of a teacher to a course."""
        mock_get_current_user.return_value = "instructor@test.com"
        mock_instructor.is_admin = False

        mock_user_service.get_user.side_effect = [mock_instructor, mock_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.teachers.TeacherPolicy.assert_instructor_access") as mock_assert_instructor,
            patch("src.routers.teachers.TeacherPolicy.assert_not_teacher") as mock_assert_not_teacher,
            patch("src.routers.teachers.StudentPolicy.assert_not_student") as mock_assert_not_student,
            patch("src.routers.teachers.ParentPolicy.assert_not_parent") as mock_assert_not_parent,
        ):
            result = await invite_teacher(
                mock_course.course_id, mock_teacher.email, mock_db, "instructor@test.com",
            )

        assert result.success is True
        mock_user_service.get_user.assert_any_call("instructor@test.com")
        mock_user_service.get_user.assert_any_call(mock_teacher.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_instructor.assert_called_once_with(mock_instructor, mock_course)
        mock_assert_not_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_not_student.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_not_parent.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_teacher_service.invite_teacher.assert_called_once_with(mock_teacher, mock_course)
        mock_personalization_service.add_course_participant.assert_called_once_with(mock_course, mock_teacher)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status", "policy_module", "policy_name"),
        [
            ("teacher_conflict", teacher_errors.TeacherRoleConflictError("teacher@test.com", "course-123"), 409, "TeacherPolicy", "assert_not_teacher"),
            ("student_conflict", student_errors.StudentRoleConflictError("student@test.com", "course-123"), 409, "StudentPolicy", "assert_not_student"),
            ("parent_conflict", parent_errors.ParentRoleConflictError("parent@test.com", "course-123"), 409, "ParentPolicy", "assert_not_parent"),
        ],
    )
    async def test_invite_teacher_role_conflicts(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_teacher_service: MagicMock,
        mock_personalization_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_instructor: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
        policy_module: str,
        policy_name: str,
    ) -> None:
        """Test role conflict scenarios when inviting a teacher to a course."""
        mock_get_current_user.return_value = "instructor@test.com"
        mock_instructor.is_admin = False
        mock_user_service.get_user.side_effect = [mock_instructor, mock_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.teachers.TeacherPolicy.assert_instructor_access") as mock_assert_instructor,
            patch("src.routers.teachers.TeacherPolicy.assert_not_teacher") as mock_assert_not_teacher,
            patch("src.routers.teachers.StudentPolicy.assert_not_student") as mock_assert_not_student,
            patch("src.routers.teachers.ParentPolicy.assert_not_parent") as mock_assert_not_parent,
        ):
            if policy_module == "TeacherPolicy" and policy_name == "assert_not_teacher":
                mock_assert_not_teacher.side_effect = side_effect
            elif policy_module == "StudentPolicy" and policy_name == "assert_not_student":
                mock_assert_not_student.side_effect = side_effect
            elif policy_module == "ParentPolicy" and policy_name == "assert_not_parent":
                mock_assert_not_parent.side_effect = side_effect

            with pytest.raises(HTTPException) as exc_info:
                await invite_teacher(
                    mock_course.course_id, mock_teacher.email, mock_db, "instructor@test.com",
                )

            assert exc_info.value.status_code == expected_status

            mock_assert_instructor.assert_called_once()

            if error_scenario == "teacher_conflict":
                mock_assert_not_teacher.assert_called_once()
                mock_assert_not_student.assert_not_called()
                mock_assert_not_parent.assert_not_called()
            elif error_scenario == "student_conflict":
                mock_assert_not_teacher.assert_called_once()
                mock_assert_not_student.assert_called_once()
                mock_assert_not_parent.assert_not_called()
            elif error_scenario == "parent_conflict":
                mock_assert_not_teacher.assert_called_once()
                mock_assert_not_student.assert_called_once()
                mock_assert_not_parent.assert_called_once()

        mock_teacher_service.invite_teacher.assert_not_called()
        mock_personalization_service.add_course_participant.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        ("user_email", "is_admin", "expected_instructor_calls"),
        [
            ("instructor@test.com", False, 1),
            ("admin@test.com", True, 2),
        ],
        ids=["as_instructor", "as_admin"],
    )
    async def test_remove_teacher_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_teacher_service: MagicMock,
        mock_personalization_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_instructor: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
        user_email: str,
        is_admin: bool,
        expected_instructor_calls: int,
    ) -> None:
        """Test the successful removal of a teacher from a course."""
        mock_get_current_user.return_value = user_email
        mock_instructor.is_admin = is_admin

        if is_admin:
            mock_admin = MagicMock()
            mock_admin.is_admin = True
            mock_admin.email = user_email
            mock_course.instructor = mock_instructor.email
            mock_user_service.get_user.side_effect = [mock_admin, mock_instructor, mock_teacher]
        else:
            mock_user_service.get_user.side_effect = [mock_instructor, mock_teacher]

        mock_course_service.get_course.return_value = mock_course

        with patch("src.routers.teachers.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
            if not is_admin:
                with patch("src.routers.teachers.TeacherPolicy.assert_instructor_access") as mock_assert_instructor:
                    result = await remove_teacher(
                        mock_course.course_id, mock_teacher.email, mock_db, user_email,
                    )
                    mock_assert_instructor.assert_called_once_with(mock_instructor, mock_course)
            else:
                result = await remove_teacher(
                    mock_course.course_id, mock_teacher.email, mock_db, user_email,
                )

            mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)

        assert result.success is True
        assert mock_user_service.get_user.call_count == expected_instructor_calls + 1
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_teacher_service.remove_teacher.assert_called_once_with(mock_teacher, mock_course)
        mock_personalization_service.remove_course_participant.assert_called_once_with(mock_course, mock_teacher)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status", "should_check_policies"),
        [
            ("instructor_not_found", user_errors.UserNotFoundError("instructor@test.com"), 401, False),
            ("teacher_not_found", [MagicMock(), user_errors.UserNotFoundError("teacher@test.com")], 400, True),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("instructor_role_required", teacher_errors.InstructorRoleRequiredError("teacher@test.com", "course-123"), 403, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("not_teacher@test.com", "course-123"), 422, True),
        ],
        ids=[
            "instructor_not_found",
            "teacher_not_found",
            "course_not_found",
            "instructor_role_required",
            "teacher_role_required",
        ],
    )
    async def test_remove_teacher_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_teacher_service: MagicMock,
        mock_personalization_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_instructor: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
        should_check_policies: bool,
    ) -> None:
        """Test error scenarios for removing a teacher from a course."""
        mock_get_current_user.return_value = "instructor@test.com"
        mock_instructor.is_admin = False

        if error_scenario in ("instructor_not_found", "teacher_not_found"):
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_instructor, mock_teacher]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.teachers.TeacherPolicy.assert_instructor_access") as mock_assert_instructor,
            patch("src.routers.teachers.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
        ):
            if error_scenario == "instructor_role_required":
                mock_assert_instructor.side_effect = side_effect
            elif error_scenario == "teacher_role_required":
                mock_assert_teacher.side_effect = side_effect
            with pytest.raises(HTTPException) as exc_info:
                await remove_teacher(
                    mock_course.course_id, mock_teacher.email, mock_db, "instructor@test.com",
                )

            assert exc_info.value.status_code == expected_status

        mock_teacher_service.remove_teacher.assert_not_called()
        mock_personalization_service.remove_course_participant.assert_not_called()
        mock_db.commit.assert_not_called()

    async def test_change_course_instructor_success(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_teacher_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_instructor: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
    ) -> None:
        """Test the successful change of a course instructor."""
        mock_get_current_user.return_value = "instructor@test.com"
        mock_instructor.is_admin = False

        mock_user_service.get_user.side_effect = [mock_instructor, mock_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.teachers.TeacherPolicy.assert_instructor_access") as mock_assert_instructor,
            patch("src.routers.teachers.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
        ):
            result = await change_course_instructor(
                mock_course.course_id, mock_teacher.email, mock_db, "instructor@test.com",
            )

        assert result.success is True
        mock_user_service.get_user.assert_any_call("instructor@test.com")
        mock_user_service.get_user.assert_any_call(mock_teacher.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_instructor.assert_called_once_with(mock_instructor, mock_course)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_teacher_service.change_course_instructor.assert_called_once_with(mock_instructor, mock_teacher, mock_course)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        ("error_scenario", "side_effect", "expected_status", "should_check_policies"),
        [
            ("instructor_not_found", user_errors.UserNotFoundError("instructor@test.com"), 401, False),
            ("new_instructor_not_found", [MagicMock(), user_errors.UserNotFoundError("teacher@test.com")], 404, True),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("instructor_role_required", teacher_errors.InstructorRoleRequiredError("teacher@test.com", "course-123"), 403, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("not_teacher@test.com", "course-123"), 422, True),
        ],
        ids=[
            "instructor_not_found",
            "new_instructor_not_found",
            "course_not_found",
            "instructor_role_required",
            "teacher_role_required",
        ],
    )
    async def test_change_course_instructor_errors(
        self,
        mock_db: MagicMock,
        mock_user_service: MagicMock,
        mock_course_service: MagicMock,
        mock_teacher_service: MagicMock,
        mock_get_current_user: MagicMock,
        mock_instructor: MagicMock,
        mock_teacher: MagicMock,
        mock_course: MagicMock,
        error_scenario: str,
        side_effect: Exception,
        expected_status: int,
        should_check_policies: bool,
    ) -> None:
        """Test error scenarios for changing a course instructor."""
        mock_get_current_user.return_value = "instructor@test.com"
        mock_instructor.is_admin = False

        if error_scenario in ("instructor_not_found", "new_instructor_not_found"):
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_instructor, mock_teacher]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.teachers.TeacherPolicy.assert_instructor_access") as mock_assert_instructor,
            patch("src.routers.teachers.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
        ):
            if error_scenario == "instructor_role_required":
                mock_assert_instructor.side_effect = side_effect
            elif error_scenario == "teacher_role_required":
                mock_assert_teacher.side_effect = side_effect
            with pytest.raises(HTTPException) as exc_info:
                await change_course_instructor(mock_course.course_id, mock_teacher.email, mock_db, "instructor@test.com")

            assert exc_info.value.status_code == expected_status

        mock_teacher_service.change_course_instructor.assert_not_called()
        mock_db.commit.assert_not_called()
