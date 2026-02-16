from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import courses as course_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.routers.courses import (
    create_course,
    delete_course,
    get_available_courses,
    get_course_info,
    leave_course,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user_service():
    with patch("src.routers.courses.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service():
    with patch("src.routers.courses.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_personalization_service():
    with patch("src.routers.courses.PersonalizationService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_section_service():
    with patch("src.routers.courses.SectionService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_student_service():
    with patch("src.routers.courses.StudentService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_teacher_service():
    with patch("src.routers.courses.TeacherService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_parent_service():
    with patch("src.routers.courses.ParentService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user():
    with patch("src.routers.courses.get_current_user") as mock_func:
        yield mock_func


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.isadmin = False
    user.email = "user@test.com"
    return user


@pytest.fixture
def mock_course():
    course = MagicMock()
    course.course_id = "course-123"
    course.title = "Test Course"
    return course


class TestCoursesRouter:

    async def test_get_available_courses_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_get_current_user,
        mock_user,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.return_value = mock_user

        mock_courses = [MagicMock(), MagicMock()]
        for i, course in enumerate(mock_courses):
            course.course_id = f"course-{i+1}"
            course.title = f"Course {i+1}"
        mock_course_service.get_available_courses.return_value = mock_courses

        with patch("src.routers.courses.Course.model_validate") as mock_validate:
            mock_validate.side_effect = lambda x: {"course_id": x.course_id, "title": x.title}
            result = await get_available_courses(mock_db, "user@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_available_courses.assert_called_once_with(mock_user)
        assert mock_validate.call_count == 2

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
        ],
    )
    async def test_get_available_courses_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_get_current_user,
        error_scenario,
        side_effect,
        expected_status,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            await get_available_courses(mock_db, "user@test.com")

        assert exc_info.value.status_code == expected_status
        mock_course_service.get_available_courses.assert_not_called()

    @pytest.mark.parametrize(
        "organization,expected_org",
        [
            ("Test Org", "Test Org"),
            (None, None),
        ],
        ids=["with_organization", "without_organization"],
    )
    async def test_create_course_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_personalization_service,
        mock_section_service,
        mock_get_current_user,
        mock_user,
        organization,
        expected_org,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.return_value = mock_user

        mock_course = MagicMock()
        mock_course.course_id = "new-course-123"
        mock_course_service.create_course.return_value = mock_course

        with patch("src.routers.courses.CourseID.model_validate") as mock_validate:
            expected_result = {"course_id": "new-course-123"}
            mock_validate.return_value = expected_result
            result = await create_course(
                mock_db, "user@test.com", "Test Course", organization,
            )

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.create_course.assert_called_once_with(
            "Test Course", expected_org, mock_user,
        )
        mock_personalization_service.add_course_participant.assert_called_once_with(mock_course, mock_user)
        mock_section_service.create_section.assert_called_once_with("General", mock_course)
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_course)

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
        ],
    )
    async def test_create_course_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_personalization_service,
        mock_section_service,
        mock_get_current_user,
        error_scenario,
        side_effect,
        expected_status,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            await create_course(mock_db, "user@test.com", "Test Course", "Test Org")

        assert exc_info.value.status_code == expected_status
        mock_course_service.create_course.assert_not_called()
        mock_personalization_service.add_course_participant.assert_not_called()
        mock_section_service.create_section.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        "user_email,is_admin,should_check_instructor,expected_status",
        [
            ("instructor@test.com", False, True, None),
            ("admin@test.com", True, False, None),
        ],
        ids=["as_instructor", "as_admin"],
    )
    async def test_delete_course_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        user_email,
        is_admin,
        should_check_instructor,
        expected_status,
    ) -> None:
        mock_get_current_user.return_value = user_email
        mock_user.isadmin = is_admin
        mock_user.email = user_email

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        if should_check_instructor:
            with patch("src.routers.courses.TeacherPolicy.assert_instructor_access") as mock_assert_instructor:
                result = await delete_course(mock_course.course_id, mock_db, user_email)
                mock_assert_instructor.assert_called_once_with(mock_user, mock_course, mock_db)
        else:
            with patch("src.routers.courses.TeacherPolicy.assert_instructor_access") as mock_assert_instructor:
                result = await delete_course(mock_course.course_id, mock_db, user_email)
                mock_assert_instructor.assert_not_called()

        assert isinstance(result, Success)
        assert result.success is True
        mock_user_service.get_user.assert_called_once_with(user_email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_course_service.delete_course.assert_called_once_with(mock_course)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400),
            ("instructor_role_required", teacher_errors.InstructorRoleRequiredError("student@test.com", "course-123"), 403),
        ],
        ids=["user_not_found", "course_not_found", "instructor_role_required"],
    )
    async def test_delete_course_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_get_current_user,
        mock_user,
        error_scenario,
        side_effect,
        expected_status,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user.isadmin = False

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            if error_scenario == "instructor_role_required":
                with patch("src.routers.courses.TeacherPolicy.assert_instructor_access") as mock_assert:
                    mock_assert.side_effect = side_effect
                    await delete_course("course-123", mock_db, "user@test.com")
            else:
                await delete_course("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == expected_status
        mock_course_service.delete_course.assert_not_called()
        mock_db.commit.assert_not_called()

    async def test_get_course_info_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_get_current_user,
        mock_user,
        mock_course,
    ) -> None:
        mock_get_current_user.return_value = "student@test.com"
        mock_user.isadmin = False
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.courses.CoursePolicy.assert_course_access") as mock_assert_access,
            patch("src.routers.courses.Course.model_validate") as mock_validate,
        ):
            expected_result = {"course_id": mock_course.course_id, "title": mock_course.title}
            mock_validate.return_value = expected_result
            result = await get_course_info(mock_course.course_id, mock_db, "student@test.com")

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_validate.assert_called_once_with(mock_course)

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400),
            ("participant_role_required", course_errors.ParticipantRoleRequiredError("user@test.com", "course-123"), 403),
        ],
        ids=["user_not_found", "course_not_found", "participant_role_required"],
    )
    async def test_get_course_info_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_get_current_user,
        mock_user,
        error_scenario,
        side_effect,
        expected_status,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user.isadmin = False

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = MagicMock()

        with patch("src.routers.courses.Course.model_validate") as mock_validate:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "participant_role_required":
                    with patch("src.routers.courses.CoursePolicy.assert_course_access") as mock_assert:
                        mock_assert.side_effect = side_effect
                        await get_course_info("course-123", mock_db, "user@test.com")
                else:
                    await get_course_info("course-123", mock_db, "user@test.com")

            assert exc_info.value.status_code == expected_status
            mock_validate.assert_not_called()

    @pytest.mark.parametrize(
        "role,check_values,service_to_check,service_to_call",
        [
            ("student", (True, False, False, False), "StudentService", "remove_student"),
            ("teacher", (False, True, False, False), "TeacherService", "remove_teacher"),
            ("parent", (False, False, True, False), "ParentService", "remove_parent"),
        ],
        ids=["as_student", "as_teacher", "as_parent"],
    )
    async def test_leave_course_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_student_service,
        mock_teacher_service,
        mock_parent_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        role,
        check_values,
        service_to_check,
        service_to_call,
    ) -> None:
        mock_get_current_user.return_value = f"{role}@test.com"
        mock_user.email = f"{role}@test.com"
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        student_check, teacher_check, parent_check, instructor_check = check_values

        with (
            patch("src.routers.courses.StudentPolicy.check_student_access", return_value=student_check),
            patch("src.routers.courses.TeacherPolicy.check_teacher_access", return_value=teacher_check),
            patch("src.routers.courses.ParentPolicy.check_parent_access", return_value=parent_check),
            patch("src.routers.courses.TeacherPolicy.check_instructor_access", return_value=instructor_check),
        ):
            result = await leave_course(mock_course.course_id, mock_db, f"{role}@test.com")

        assert result.success is True

        if service_to_check == "StudentService":
            mock_student_service.remove_student.assert_called_once_with(mock_user, mock_course)
            mock_teacher_service.remove_teacher.assert_not_called()
            mock_parent_service.remove_parent.assert_not_called()
        elif service_to_check == "TeacherService":
            mock_teacher_service.remove_teacher.assert_called_once_with(mock_user, mock_course)
            mock_student_service.remove_student.assert_not_called()
            mock_parent_service.remove_parent.assert_not_called()
        elif service_to_check == "ParentService":
            mock_parent_service.remove_parent.assert_called_once_with(mock_user, mock_course)
            mock_student_service.remove_student.assert_not_called()
            mock_teacher_service.remove_teacher.assert_not_called()

        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "role,check_values,expected_error",
        [
            ("instructor", (False, False, False, True), "primary instructor"),
            ("non_participant", (False, False, False, False), "not a participant"),
        ],
        ids=["as_instructor", "no_role"],
    )
    async def test_leave_course_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_student_service,
        mock_teacher_service,
        mock_parent_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        role,
        check_values,
        expected_error,
    ) -> None:
        mock_get_current_user.return_value = f"{role}@test.com"
        mock_user.email = f"{role}@test.com"
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        student_check, teacher_check, parent_check, instructor_check = check_values

        with (
            patch("src.routers.courses.StudentPolicy.check_student_access", return_value=student_check),
            patch("src.routers.courses.TeacherPolicy.check_teacher_access", return_value=teacher_check),
            patch("src.routers.courses.ParentPolicy.check_parent_access", return_value=parent_check),
            patch("src.routers.courses.TeacherPolicy.check_instructor_access", return_value=instructor_check),
            pytest.raises(HTTPException) as exc_info,
        ):
            await leave_course(mock_course.course_id, mock_db, f"{role}@test.com")

        assert exc_info.value.status_code == 403
        assert expected_error in str(exc_info.value.detail).lower()

        mock_student_service.remove_student.assert_not_called()
        mock_teacher_service.remove_teacher.assert_not_called()
        mock_parent_service.remove_parent.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400),
        ],
        ids=["user_not_found", "course_not_found"],
    )
    async def test_leave_course_base_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_get_current_user,
        mock_user,
        error_scenario,
        side_effect,
        expected_status,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user
            mock_course_service.get_course.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            await leave_course("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == expected_status
