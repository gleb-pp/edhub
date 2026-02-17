from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import courses as course_errors
from src.exceptions import parents as parent_errors
from src.exceptions import students as student_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.routers.students import get_enrolled_students, invite_student, remove_student

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user_service():
    with patch("src.routers.students.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service():
    with patch("src.routers.students.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_student_service():
    with patch("src.routers.students.StudentService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_personalization_service():
    with patch("src.routers.students.PersonalizationService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user():
    with patch("src.routers.students.get_current_user") as mock_func:
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
def mock_student():
    student = MagicMock()
    student.email = "student@test.com"
    return student


@pytest.fixture
def mock_course():
    course = MagicMock()
    course.course_id = "course-123"
    return course


class TestStudentsRouter:

    async def test_get_enrolled_students_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_student_service,
        mock_get_current_user,
        mock_user,
        mock_course,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"
        mock_user.isadmin = False
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        mock_students = [MagicMock(), MagicMock()]
        mock_student_service.get_enrolled_students.return_value = mock_students

        with (
            patch("src.routers.students.CoursePolicy.assert_course_access") as mock_assert_access,
            patch("src.routers.students.User.model_validate") as mock_validate,
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_enrolled_students(mock_course.course_id, mock_db, "user@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_student_service.get_enrolled_students.assert_called_once_with(mock_course)
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
    async def test_get_enrolled_students_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_student_service,
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

        with patch("src.routers.students.CoursePolicy.assert_course_access") as mock_assert_access:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "participant_role_required":
                    mock_assert_access.side_effect = side_effect

                await get_enrolled_students(mock_course.course_id, mock_db, "user@test.com")

            assert exc_info.value.status_code == expected_status

            if should_check_policy:
                mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

        with patch("src.routers.students.User.model_validate") as mock_validate:
            mock_validate.assert_not_called()

    async def test_invite_student_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_student_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_course,
    ) -> None:
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.students.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.students.StudentPolicy.assert_not_student") as mock_assert_not_student,
            patch("src.routers.students.TeacherPolicy.assert_not_teacher") as mock_assert_not_teacher,
            patch("src.routers.students.ParentPolicy.assert_not_parent") as mock_assert_not_parent,
        ):
            result = await invite_student(
                mock_course.course_id, mock_student.email, mock_db, "teacher@test.com",
            )

        assert result.success is True
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call(mock_student.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_not_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assert_not_teacher.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assert_not_parent.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_student_service.invite_student.assert_called_once_with(mock_student, mock_course)
        mock_personalization_service.add_course_participant.assert_called_once_with(mock_course, mock_student)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policies",
        [
            ("teacher_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("student_not_found", [MagicMock(), user_errors.UserNotFoundError("student@test.com")], 404, True),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
            ("student_conflict", student_errors.StudentRoleConflictError("student@test.com", "course-123"), 409, True),
        ],
        ids=[
            "teacher_not_found",
            "student_not_found",
            "course_not_found",
            "teacher_role_required",
            "student_conflict",
        ],
    )
    async def test_invite_student_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_student_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policies,
    ) -> None:
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        if error_scenario in ("teacher_not_found", "student_not_found"):
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_teacher, mock_student]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.students.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.students.StudentPolicy.assert_not_student") as mock_assert_not_student,
        ):
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "teacher_role_required":
                    mock_assert_teacher.side_effect = side_effect
                elif error_scenario == "student_conflict":
                    mock_assert_not_student.side_effect = side_effect

                await invite_student(
                    mock_course.course_id, mock_student.email, mock_db, "teacher@test.com",
                )

            assert exc_info.value.status_code == expected_status

        mock_student_service.invite_student.assert_not_called()
        mock_personalization_service.add_course_participant.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,policy_module,policy_name",
        [
            ("student_conflict", student_errors.StudentRoleConflictError("student@test.com", "course-123"), 409, "StudentPolicy", "assert_not_student"),
            ("teacher_conflict", teacher_errors.TeacherRoleConflictError("teacher@test.com", "course-123"), 409, "TeacherPolicy", "assert_not_teacher"),
            ("parent_conflict", parent_errors.ParentRoleConflictError("parent@test.com", "course-123"), 409, "ParentPolicy", "assert_not_parent"),
        ],
    )
    async def test_invite_student_role_conflicts(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_student_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        policy_module,
        policy_name,
    ) -> None:
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False
        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.students.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.students.StudentPolicy.assert_not_student") as mock_assert_not_student,
            patch("src.routers.students.TeacherPolicy.assert_not_teacher") as mock_assert_not_teacher,
            patch("src.routers.students.ParentPolicy.assert_not_parent") as mock_assert_not_parent,
        ):
            if policy_module == "StudentPolicy" and policy_name == "assert_not_student":
                mock_assert_not_student.side_effect = side_effect
            elif policy_module == "TeacherPolicy" and policy_name == "assert_not_teacher":
                mock_assert_not_teacher.side_effect = side_effect
            elif policy_module == "ParentPolicy" and policy_name == "assert_not_parent":
                mock_assert_not_parent.side_effect = side_effect

            with pytest.raises(HTTPException) as exc_info:
                await invite_student(
                    mock_course.course_id, mock_student.email, mock_db, "teacher@test.com",
                )

            assert exc_info.value.status_code == expected_status

            mock_assert_teacher.assert_called_once()

            if error_scenario == "student_conflict":
                mock_assert_not_student.assert_called_once()
                mock_assert_not_teacher.assert_not_called()
                mock_assert_not_parent.assert_not_called()
            elif error_scenario == "teacher_conflict":
                mock_assert_not_student.assert_called_once()
                mock_assert_not_teacher.assert_called_once()
                mock_assert_not_parent.assert_not_called()
            elif error_scenario == "parent_conflict":
                mock_assert_not_student.assert_called_once()
                mock_assert_not_teacher.assert_called_once()
                mock_assert_not_parent.assert_called_once()

        mock_student_service.invite_student.assert_not_called()
        mock_personalization_service.add_course_participant.assert_not_called()
        mock_db.commit.assert_not_called()

    async def test_remove_student_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_student_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_course,
    ) -> None:
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.students.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.students.StudentPolicy.assert_student_access") as mock_assert_student,
        ):
            result = await remove_student(
                mock_course.course_id, mock_student.email, mock_db, "teacher@test.com",
            )

        assert result.success is True
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call(mock_student.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_student_service.remove_student.assert_called_once_with(mock_student, mock_course)
        mock_personalization_service.remove_course_participant.assert_called_once_with(mock_course, mock_student)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policies",
        [
            ("teacher_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("student_not_found", [MagicMock(), user_errors.UserNotFoundError("student@test.com")], 404, True),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
            ("student_role_required", student_errors.StudentRoleRequiredError("student@test.com", "course-123"), 422, True),
        ],
        ids=[
            "teacher_not_found",
            "student_not_found",
            "course_not_found",
            "teacher_role_required",
            "student_role_required",
        ],
    )
    async def test_remove_student_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_student_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policies,
    ) -> None:
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        if error_scenario in ("teacher_not_found", "student_not_found"):
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_teacher, mock_student]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.students.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.students.StudentPolicy.assert_student_access") as mock_assert_student,
        ):
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "teacher_role_required":
                    mock_assert_teacher.side_effect = side_effect
                elif error_scenario == "student_role_required":
                    mock_assert_student.side_effect = side_effect

                await remove_student(
                    mock_course.course_id, mock_student.email, mock_db, "teacher@test.com",
                )

            assert exc_info.value.status_code == expected_status

        mock_student_service.remove_student.assert_not_called()
        mock_personalization_service.remove_course_participant.assert_not_called()
        mock_db.commit.assert_not_called()
