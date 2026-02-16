import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.exceptions import courses as course_errors
from src.exceptions import parents as parent_errors
from src.exceptions import students as student_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.routers.parents import (
    get_students_parents,
    invite_parent,
    remove_parent,
    get_parents_children
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user_service():
    with patch("src.routers.parents.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service():
    with patch("src.routers.parents.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_parent_service():
    with patch("src.routers.parents.ParentService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_personalization_service():
    with patch("src.routers.parents.PersonalizationService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user():
    with patch("src.routers.parents.get_current_user") as mock_func:
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
def mock_parent():
    parent = MagicMock()
    parent.email = "parent@test.com"
    return parent


@pytest.fixture
def mock_course():
    course = MagicMock()
    course.course_id = "course-123"
    return course


class TestParentsRouter:

    async def test_get_students_parents_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_parent_service,
        mock_get_current_user,
        mock_user,
        mock_student,
        mock_course,
    ):
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course

        mock_parents = [MagicMock(), MagicMock()]
        mock_parent_service.get_students_parents.return_value = mock_parents

        with (
            patch("src.routers.parents.StudentPolicy.assert_access_to_student") as mock_assert_access,
            patch("src.routers.parents.User.model_validate") as mock_validate
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_students_parents(
                mock_course.course_id, mock_student.email, mock_db, "user@test.com"
            )

        assert len(result) == 2
        mock_user_service.get_user.assert_any_call("user@test.com")
        mock_user_service.get_user.assert_any_call(mock_student.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_student, mock_user, mock_course, mock_db)
        mock_parent_service.get_students_parents.assert_called_once_with(mock_student, mock_course)
        assert mock_validate.call_count == 2

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_access",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("student_not_found", [MagicMock(), user_errors.UserNotFoundError("student@test.com")], 400, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("student_role_required", student_errors.StudentRoleRequiredError("student@test.com", "course-123"), 400, True),
            ("access_denied", student_errors.NoAccessToStudentInfoError("student@test.com", "user@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "student_not_found", "course_not_found", "student_role_required", "access_denied"]
    )
    async def test_get_students_parents_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_parent_service,
        mock_get_current_user,
        mock_user,
        mock_student,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_access,
    ):
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        elif error_scenario == "student_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_user, mock_student]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with patch("src.routers.parents.StudentPolicy.assert_access_to_student") as mock_assert_access:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario in ["student_role_required", "access_denied"]:
                    mock_assert_access.side_effect = side_effect

                await get_students_parents(
                    mock_course.course_id, mock_student.email, mock_db, "user@test.com"
                )

            assert exc_info.value.status_code == expected_status

            if should_check_access:
                mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

        with patch("src.routers.parents.User.model_validate") as mock_validate:
            mock_validate.assert_not_called()

    @pytest.mark.parametrize(
        "parent_already_in_course",
        [False, True],
        ids=["parent_not_in_course", "parent_already_in_course"]
    )
    async def test_invite_parent_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_parent_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_parent,
        mock_course,
        parent_already_in_course,
    ):
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.parents.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.parents.StudentPolicy.assert_student_access") as mock_assert_student,
            patch("src.routers.parents.TeacherPolicy.assert_not_teacher") as mock_assert_not_teacher,
            patch("src.routers.parents.StudentPolicy.assert_not_student") as mock_assert_not_student,
            patch("src.routers.parents.ParentPolicy.assert_not_parent_of_student") as mock_assert_not_parent,
            patch("src.routers.parents.ParentPolicy.check_parent_access", return_value=parent_already_in_course)
        ):
            result = await invite_parent(
                mock_course.course_id,
                mock_student.email,
                mock_parent.email,
                mock_db,
                "teacher@test.com",
            )

        assert result.success is True
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call(mock_student.email)
        mock_user_service.get_user.assert_any_call(mock_parent.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assert_not_teacher.assert_called_once_with(mock_parent, mock_course, mock_db)
        mock_assert_not_student.assert_called_once_with(mock_parent, mock_course, mock_db)
        mock_assert_not_parent.assert_called_once_with(mock_parent, mock_student, mock_course, mock_db)

        if parent_already_in_course:
            mock_personalization_service.add_course_participant.assert_not_called()
        else:
            mock_personalization_service.add_course_participant.assert_called_once_with(mock_course, mock_parent)

        mock_parent_service.invite_parent.assert_called_once_with(mock_parent, mock_student, mock_course)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_call_policies",
        [
            ("teacher_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("student_not_found", [MagicMock(), user_errors.UserNotFoundError("student@test.com")], 400, True),
            ("parent_not_found", [MagicMock(), MagicMock(), user_errors.UserNotFoundError("parent@test.com")], 400, True),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
            ("student_role_required", student_errors.StudentRoleRequiredError("student@test.com", "course-123"), 400, True),
            ("teacher_conflict", teacher_errors.TeacherRoleConflictError("parent@test.com", "course-123"), 409, True),
            ("student_conflict", student_errors.StudentRoleConflictError("parent@test.com", "course-123"), 409, True),
            ("parent_already_exists", parent_errors.ParentOfStudentRoleConflictError("parent@test.com", "student@test.com", "course-123"), 409, True),
        ],
        ids=[
            "teacher_not_found",
            "student_not_found",
            "parent_not_found",
            "course_not_found",
            "teacher_role_required",
            "student_role_required",
            "teacher_conflict",
            "student_conflict",
            "parent_already_exists"
        ]
    )
    async def test_invite_parent_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_parent_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_parent,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_call_policies,
    ):
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        if error_scenario in ["teacher_not_found", "student_not_found", "parent_not_found"]:
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.parents.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.parents.StudentPolicy.assert_student_access") as mock_assert_student,
            patch("src.routers.parents.TeacherPolicy.assert_not_teacher") as mock_assert_not_teacher,
            patch("src.routers.parents.StudentPolicy.assert_not_student") as mock_assert_not_student,
            patch("src.routers.parents.ParentPolicy.assert_not_parent_of_student") as mock_assert_not_parent,
            patch("src.routers.parents.ParentPolicy.check_parent_access", return_value=False)
        ):
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "teacher_role_required":
                    mock_assert_teacher.side_effect = side_effect
                elif error_scenario == "student_role_required":
                    mock_assert_student.side_effect = side_effect
                elif error_scenario == "teacher_conflict":
                    mock_assert_not_teacher.side_effect = side_effect
                elif error_scenario == "student_conflict":
                    mock_assert_not_student.side_effect = side_effect
                elif error_scenario == "parent_already_exists":
                    mock_assert_not_parent.side_effect = side_effect

                await invite_parent(
                    mock_course.course_id,
                    mock_student.email,
                    mock_parent.email,
                    mock_db,
                    "teacher@test.com",
                )

            assert exc_info.value.status_code == expected_status

        mock_parent_service.invite_parent.assert_not_called()
        mock_personalization_service.add_course_participant.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.parametrize(
        "parent_still_in_course",
        [False, True],
        ids=["parent_removed", "parent_still_in_course"]
    )
    async def test_remove_parent_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_parent_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_parent,
        mock_course,
        parent_still_in_course,
    ):
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.parents.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.parents.StudentPolicy.assert_student_access") as mock_assert_student,
            patch("src.routers.parents.ParentPolicy.assert_parent_of_student") as mock_assert_parent,
            patch("src.routers.parents.ParentPolicy.check_parent_access", return_value=parent_still_in_course)
        ):
            result = await remove_parent(
                mock_course.course_id,
                mock_student.email,
                mock_parent.email,
                mock_db,
                "teacher@test.com",
            )

        assert result.success is True
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assert_parent.assert_called_once_with(mock_parent, mock_student, mock_course, mock_db)
        mock_parent_service.remove_parent_student.assert_called_once_with(mock_parent, mock_student, mock_course)

        if parent_still_in_course:
            mock_personalization_service.remove_course_participant.assert_not_called()
        else:
            mock_personalization_service.remove_course_participant.assert_called_once_with(mock_course, mock_parent)

        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policies",
        [
            ("teacher_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("student_not_found", [MagicMock(), user_errors.UserNotFoundError("student@test.com")], 400, True),
            ("parent_not_found", [MagicMock(), MagicMock(), user_errors.UserNotFoundError("parent@test.com")], 400, True),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("parent_role_required", parent_errors.ParentOfStudentRoleRequiredError("parent@test.com", "student@test.com", "course-123"), 400, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
        ],
        ids=[
            "teacher_not_found",
            "student_not_found",
            "parent_not_found",
            "course_not_found",
            "parent_role_required",
            "teacher_role_required"
        ]
    )
    async def test_remove_parent_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_parent_service,
        mock_personalization_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_parent,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policies,
    ):
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        if error_scenario == "teacher_not_found":
            mock_user_service.get_user.side_effect = side_effect
        elif error_scenario == "student_not_found":
            mock_user_service.get_user.side_effect = side_effect
        elif error_scenario == "parent_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.parents.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.parents.StudentPolicy.assert_student_access") as mock_assert_student,
            patch("src.routers.parents.ParentPolicy.assert_parent_of_student") as mock_assert_parent,
            patch("src.routers.parents.ParentPolicy.check_parent_access", return_value=False)
        ):
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "teacher_role_required":
                    mock_assert_teacher.side_effect = side_effect
                elif error_scenario == "parent_role_required":
                    mock_assert_parent.side_effect = side_effect

                await remove_parent(
                    mock_course.course_id,
                    mock_student.email,
                    mock_parent.email,
                    mock_db,
                    "teacher@test.com",
                )

            assert exc_info.value.status_code == expected_status

        mock_parent_service.remove_parent_student.assert_not_called()
        mock_personalization_service.remove_course_participant.assert_not_called()
        mock_db.commit.assert_not_called()

    async def test_get_parents_children_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_parent_service,
        mock_get_current_user,
        mock_user,
        mock_parent,
        mock_course,
    ):
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.side_effect = [mock_user, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        mock_children = [MagicMock(), MagicMock()]
        mock_parent_service.get_parents_children.return_value = mock_children

        with (
            patch("src.routers.parents.ParentPolicy.assert_access_to_parent") as mock_assert_access,
            patch("src.routers.parents.User.model_validate") as mock_validate
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_parents_children(
                mock_course.course_id, mock_parent.email, mock_db, "user@test.com"
            )

        assert len(result) == 2
        mock_user_service.get_user.assert_any_call("user@test.com")
        mock_user_service.get_user.assert_any_call(mock_parent.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_parent, mock_user, mock_course, mock_db)
        mock_parent_service.get_parents_children.assert_called_once_with(mock_parent, mock_course)
        assert mock_validate.call_count == 2

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_access",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("parent_not_found", [MagicMock(), user_errors.UserNotFoundError("parent@test.com")], 400, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("parent_role_required", parent_errors.ParentRoleRequiredError("parent@test.com", "course-123"), 400, True),
            ("access_denied", parent_errors.NoAccessToParentInfoError("parent@test.com", "stranger@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "parent_not_found", "course_not_found", "parent_role_required", "access_denied"]
    )
    async def test_get_parents_children_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_parent_service,
        mock_get_current_user,
        mock_user,
        mock_parent,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_access,
    ):
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        elif error_scenario == "parent_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_user, mock_parent]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        with patch("src.routers.parents.ParentPolicy.assert_access_to_parent") as mock_assert_access:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario in ["parent_role_required", "access_denied"]:
                    mock_assert_access.side_effect = side_effect

                await get_parents_children(
                    mock_course.course_id, mock_parent.email, mock_db, "user@test.com"
                )

            assert exc_info.value.status_code == expected_status

            if should_check_access:
                mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

        with patch("src.routers.parents.User.model_validate") as mock_validate:
            mock_validate.assert_not_called()
