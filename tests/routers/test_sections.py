from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import courses as course_errors
from src.exceptions import sections as section_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.routers.sections import (
    change_section_order,
    create_section,
    get_course_feed,
    get_course_sections,
    remove_section,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user_service():
    with patch("src.routers.sections.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service():
    with patch("src.routers.sections.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_section_service():
    with patch("src.routers.sections.SectionService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_material_service():
    with patch("src.routers.sections.MaterialService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_assignment_service():
    with patch("src.routers.sections.AssignmentService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user():
    with patch("src.routers.sections.get_current_user") as mock_func:
        yield mock_func


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.isadmin = False
    user.email = "user@test.com"
    return user


@pytest.fixture
def mock_teacher():
    teacher = MagicMock()
    teacher.isadmin = False
    teacher.email = "teacher@test.com"
    return teacher


@pytest.fixture
def mock_course():
    course = MagicMock()
    course.course_id = "course-123"
    return course


@pytest.fixture
def mock_section():
    section = MagicMock()
    section.section_id = 1
    section.title = "Test Section"
    section.course_id = "course-123"
    return section


class TestSectionsRouter:

    async def test_get_course_sections_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_get_current_user,
        mock_user,
        mock_course,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user.isadmin = False
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        mock_sections = [MagicMock(), MagicMock()]
        mock_section_service.get_course_sections.return_value = mock_sections

        with (
            patch("src.routers.sections.CoursePolicy.assert_course_access") as mock_assert_access,
            patch("src.routers.sections.Section.model_validate") as mock_validate,
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_course_sections(mock_course.course_id, mock_db, "user@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_section_service.get_course_sections.assert_called_once_with(mock_course)
        assert mock_validate.call_count == 2

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policy",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("participant_role_required", course_errors.ParticipantRoleRequiredError("user@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "course_not_found", "participant_role_required"],
    )
    async def test_get_course_sections_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policy,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with patch("src.routers.sections.CoursePolicy.assert_course_access") as mock_assert_access:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "participant_role_required":
                    mock_assert_access.side_effect = side_effect

                await get_course_sections(mock_course.course_id, mock_db, "user@test.com")

            assert exc_info.value.status_code == expected_status

            if should_check_policy:
                mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

        with patch("src.routers.sections.Section.model_validate") as mock_validate:
            mock_validate.assert_not_called()

    async def test_get_course_feed_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_material_service,
        mock_assignment_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        mock_section,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user.isadmin = False
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

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

        mock_section_service.get_course_sections.return_value = [mock_section, mock_section2]

        def get_section_materials_side_effect(section) -> list[MagicMock]:
            return [mock_material1, mock_material2] if section.section_id == 1 else []
        mock_material_service.get_section_materials.side_effect = get_section_materials_side_effect

        def get_section_assignments_side_effect(section) -> list[MagicMock]:
            return [mock_assignment1] if section.section_id == 1 else []
        mock_assignment_service.get_section_assignments.side_effect = get_section_assignments_side_effect

        with (
            patch("src.routers.sections.CoursePolicy.assert_course_access"),
            patch("src.routers.sections.Section.model_validate") as mock_validate,
        ):
            mock_validate.side_effect = lambda x: x
            result = await get_course_feed(mock_course.course_id, mock_db, "user@test.com")

        assert len(result) == 2
        assert len(result[0].feed) == 3
        assert len(result[1].feed) == 0
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_section_service.get_course_sections.assert_called_once_with(mock_course)
        assert mock_material_service.get_section_materials.call_count == 2
        assert mock_assignment_service.get_section_assignments.call_count == 2

    async def test_get_course_feed_sorted_by_creation_time(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_material_service,
        mock_assignment_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        mock_section,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user.isadmin = False
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        mock_material1 = MagicMock()
        mock_material1.material_id = 101
        mock_material1.course_id = "course-123"
        mock_material1.section_id = 1
        mock_material1.title = "Material 3"
        mock_material1.creation_time = datetime(2024, 1, 3, tzinfo=UTC)
        mock_material1.author = "teacher@test.com"
        mock_material2 = MagicMock()
        mock_material2.material_id = 102
        mock_material2.course_id = "course-123"
        mock_material2.section_id = 1
        mock_material2.title = "Material 1"
        mock_material2.creation_time = datetime(2024, 1, 1, tzinfo=UTC)
        mock_material2.author = "teacher@test.com"
        mock_assignment1 = MagicMock()
        mock_assignment1.assignment_id = 201
        mock_assignment1.course_id = "course-123"
        mock_assignment1.section_id = 1
        mock_assignment1.title = "Assignment 1"
        mock_assignment1.creation_time = datetime(2024, 1, 2, tzinfo=UTC)
        mock_assignment1.author = "teacher@test.com"

        mock_section_service.get_course_sections.return_value = [mock_section]
        mock_material_service.get_section_materials.return_value = [mock_material1, mock_material2]
        mock_assignment_service.get_section_assignments.return_value = [mock_assignment1]

        with (
            patch("src.routers.sections.CoursePolicy.assert_course_access"),
            patch("src.routers.sections.Section.model_validate") as mock_validate,
        ):
            mock_validate.side_effect = lambda x: x
            result = await get_course_feed(mock_course.course_id, mock_db, "user@test.com")

        feed_dates = [post.creation_time for post in result[0].feed]
        assert feed_dates == [
            datetime(2024, 1, 1, tzinfo=UTC),
            datetime(2024, 1, 2, tzinfo=UTC),
            datetime(2024, 1, 3, tzinfo=UTC),
        ]

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policy",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("participant_role_required", course_errors.ParticipantRoleRequiredError("user@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "course_not_found", "participant_role_required"],
    )
    async def test_get_course_feed_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policy,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with patch("src.routers.sections.CoursePolicy.assert_course_access") as mock_assert_access:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "participant_role_required":
                    mock_assert_access.side_effect = side_effect

                await get_course_feed(mock_course.course_id, mock_db, "user@test.com")

            assert exc_info.value.status_code == expected_status

            if should_check_policy:
                mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

    @pytest.mark.parametrize(
        "user_email,is_admin,should_check_teacher",
        [
            ("teacher@test.com", False, True),
            ("admin@test.com", True, False),
        ],
        ids=["as_teacher", "as_admin"],
    )
    async def test_create_section_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_get_current_user,
        mock_teacher,
        mock_course,
        mock_section,
        user_email,
        is_admin,
        should_check_teacher,
    ) -> None:
        mock_get_current_user.return_value = user_email
        mock_teacher.isadmin = is_admin
        mock_teacher.email = user_email

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.create_section.return_value = mock_section

        expected_result = {"section_id": mock_section.section_id}

        with patch("src.routers.sections.SectionID.model_validate") as mock_validate:
            mock_validate.return_value = expected_result

            if should_check_teacher:
                with patch("src.routers.sections.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
                    result = await create_section(
                        mock_course.course_id, mock_db, user_email, "New Section",
                    )
                    mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
            else:
                with patch("src.routers.sections.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
                    result = await create_section(
                        mock_course.course_id, mock_db, user_email, "New Section",
                    )
                    mock_assert_teacher.assert_not_called()

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with(user_email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_section_service.create_section.assert_called_once_with("New Section", mock_course)
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_section)

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policy",
        [
            ("user_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "course_not_found", "teacher_role_required"],
    )
    async def test_create_section_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_get_current_user,
        mock_teacher,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policy,
    ) -> None:
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

        with patch("src.routers.sections.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "teacher_role_required":
                    mock_assert_teacher.side_effect = side_effect

                await create_section(mock_course.course_id, mock_db, "teacher@test.com", "New Section")

            assert exc_info.value.status_code == expected_status

            if should_check_policy:
                mock_assert_teacher.assert_called_once()
            else:
                mock_assert_teacher.assert_not_called()

        mock_section_service.create_section.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        "user_email,is_admin,should_check_teacher",
        [
            ("teacher@test.com", False, True),
            ("admin@test.com", True, False),
        ],
        ids=["as_teacher", "as_admin"],
    )
    async def test_change_section_order_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_get_current_user,
        mock_teacher,
        mock_course,
        user_email,
        is_admin,
        should_check_teacher,
    ) -> None:
        mock_get_current_user.return_value = user_email
        mock_teacher.isadmin = is_admin
        mock_teacher.email = user_email

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course

        new_order = [2, 1, 3]

        if should_check_teacher:
            with patch("src.routers.sections.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
                result = await change_section_order(
                    mock_course.course_id, mock_db, new_order, user_email,
                )
                mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        else:
            with patch("src.routers.sections.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
                result = await change_section_order(
                    mock_course.course_id, mock_db, new_order, user_email,
                )
                mock_assert_teacher.assert_not_called()

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with(user_email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_section_service.change_section_order.assert_called_once_with(mock_course, new_order)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policy",
        [
            ("user_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
            ("incorrect_order", section_errors.IncorrectSectionOrderError(), 400, True),
        ],
        ids=["user_not_found", "course_not_found", "teacher_role_required", "incorrect_order"],
    )
    async def test_change_section_order_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_get_current_user,
        mock_teacher,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policy,
    ) -> None:
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

        if error_scenario == "incorrect_order":
            mock_section_service.change_section_order.side_effect = side_effect

        with patch("src.routers.sections.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "teacher_role_required":
                    mock_assert_teacher.side_effect = side_effect

                await change_section_order(mock_course.course_id, mock_db, [1], "teacher@test.com")

            assert exc_info.value.status_code == expected_status

            if should_check_policy and error_scenario not in ["user_not_found", "course_not_found"]:
                mock_assert_teacher.assert_called_once()
            else:
                mock_assert_teacher.assert_not_called()

        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        "user_email,is_admin,should_check_teacher",
        [
            ("teacher@test.com", False, True),
            ("admin@test.com", True, False),
        ],
        ids=["as_teacher", "as_admin"],
    )
    async def test_remove_section_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_get_current_user,
        mock_teacher,
        mock_course,
        mock_section,
        user_email,
        is_admin,
        should_check_teacher,
    ) -> None:
        mock_get_current_user.return_value = user_email
        mock_teacher.isadmin = is_admin
        mock_teacher.email = user_email

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.return_value = mock_section

        if should_check_teacher:
            with patch("src.routers.sections.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
                result = await remove_section(
                    mock_course.course_id, mock_section.section_id, mock_db, user_email,
                )
                mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        else:
            with patch("src.routers.sections.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
                result = await remove_section(
                    mock_course.course_id, mock_section.section_id, mock_db, user_email,
                )
                mock_assert_teacher.assert_not_called()

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with(user_email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_section_service.get_section.assert_called_once_with(mock_course, mock_section.section_id)
        mock_section_service.remove_section.assert_called_once_with(mock_section)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policy",
        [
            ("user_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("section_not_found", section_errors.SectionNotFoundError(5, "course-123"), 400, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
            ("last_section", section_errors.LastSectionDeleteError(5, "course-123"), 409, True),
        ],
        ids=["user_not_found", "course_not_found", "section_not_found", "teacher_role_required", "last_section"],
    )
    async def test_remove_section_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_section_service,
        mock_get_current_user,
        mock_teacher,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policy,
    ) -> None:
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
        elif error_scenario == "last_section":
            mock_section_service.get_section.return_value = MagicMock()
            mock_section_service.remove_section.side_effect = side_effect
        else:
            mock_section_service.get_section.return_value = MagicMock()

        with patch("src.routers.sections.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "teacher_role_required":
                    mock_assert_teacher.side_effect = side_effect

                await remove_section(mock_course.course_id, 5, mock_db, "teacher@test.com")

            assert exc_info.value.status_code == expected_status

            if should_check_policy and error_scenario not in ["user_not_found", "course_not_found"]:
                mock_assert_teacher.assert_called_once()
            else:
                mock_assert_teacher.assert_not_called()

        mock_db.commit.assert_not_called()
