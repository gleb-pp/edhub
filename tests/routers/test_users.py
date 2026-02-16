import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.exceptions import admins as admin_errors
from src.exceptions import courses as course_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.routers.users import (
    get_user_info,
    get_my_role,
    create_user,
    login,
    change_password,
    get_my_instructor_courses,
    remove_user
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user_service():
    with patch("src.routers.users.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service():
    with patch("src.routers.users.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user():
    with patch("src.routers.users.get_current_user") as mock_func:
        yield mock_func


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.isadmin = False
    user.email = "user@test.com"
    user.name = "Test User"
    return user


@pytest.fixture
def mock_course():
    course = MagicMock()
    course.course_id = "course-123"
    return course


class TestUsersRouter:

    async def test_get_user_info_success(
        self,
        mock_db,
        mock_user_service,
        mock_user,
    ):
        mock_user_service.get_user.return_value = mock_user

        with patch("src.routers.users.User.model_validate") as mock_validate:
            expected_result = {"email": mock_user.email, "name": mock_user.name}
            mock_validate.return_value = expected_result
            result = await get_user_info(mock_user.email, mock_db)

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with(mock_user.email)
        mock_validate.assert_called_once_with(mock_user)

    async def test_get_user_info_not_found(
        self,
        mock_db,
        mock_user_service,
    ):
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_user_info("user@test.com", mock_db)

        assert exc_info.value.status_code == 404

    @pytest.mark.parametrize(
        "role_checks,expected_role",
        [
            ((True, False, False, False), "instructor"),
            ((False, True, False, False), "teacher"),
            ((False, False, True, False), "student"),
            ((False, False, False, True), "parent"),
            ((False, False, False, False), "none"),
        ],
        ids=["instructor", "teacher", "student", "parent", "none"]
    )
    async def test_get_my_role_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        role_checks,
        expected_role,
    ):
        mock_get_current_user.return_value = mock_user.email
        mock_user.isadmin = False
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        instructor_check, teacher_check, student_check, parent_check = role_checks

        with (
            patch("src.routers.users.TeacherPolicy.check_instructor_access", return_value=instructor_check),
            patch("src.routers.users.TeacherPolicy.check_teacher_access", return_value=teacher_check),
            patch("src.routers.users.StudentPolicy.check_student_access", return_value=student_check),
            patch("src.routers.users.ParentPolicy.check_parent_access", return_value=parent_check)
        ):
            result = await get_my_role(mock_course.course_id, mock_db, mock_user.email)

        assert result.is_instructor is instructor_check
        assert result.is_teacher is teacher_check
        assert result.is_student is student_check
        assert result.is_parent is parent_check
        assert result.is_admin is False
        mock_user_service.get_user.assert_called_once_with(mock_user.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400),
        ],
        ids=["user_not_found", "course_not_found"]
    )
    async def test_get_my_role_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_get_current_user,
        mock_user,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
    ):
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user
            mock_course_service.get_course.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            await get_my_role(mock_course.course_id, mock_db, "user@test.com")

        assert exc_info.value.status_code == expected_status

    async def test_create_user_success(
        self,
        mock_db,
        mock_user_service,
        mock_user,
    ):
        mock_user_service.create_user.return_value = mock_user
        mock_user_service.get_access_token.return_value = "jwt_token"

        result = await create_user(mock_user.email, "Test User", "Pass123!@#", mock_db)

        assert result.access_token == "jwt_token"
        mock_user_service.validate_user_email.assert_called_once_with(mock_user.email)
        mock_user_service.validate_user_name.assert_called_once_with("Test User")
        mock_user_service.validate_password_length.assert_called_once_with("Pass123!@#")
        mock_user_service.create_user.assert_called_once_with(mock_user.email, "Test User", "Pass123!@#")
        mock_user_service.get_access_token.assert_called_once_with(mock_user)

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("validation_error", user_errors.EmailFormatError(), 422),
            ("user_exists", user_errors.UserExistsError("user@test.com"), 409),
        ],
        ids=["validation_error", "user_exists"]
    )
    async def test_create_user_errors(
        self,
        mock_db,
        mock_user_service,
        error_scenario,
        side_effect,
        expected_status,
    ):
        if error_scenario == "validation_error":
            mock_user_service.validate_user_email.side_effect = side_effect
        else:
            mock_user_service.validate_user_email.return_value = None
            mock_user_service.validate_user_name.return_value = None
            mock_user_service.validate_password_length.return_value = None
            mock_user_service.create_user.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            await create_user("user@test.com", "Test User", "Pass123!@#", mock_db)

        assert exc_info.value.status_code == expected_status

    async def test_login_success(
        self,
        mock_db,
        mock_user_service,
        mock_user,
    ):
        mock_user_service.get_user.return_value = mock_user
        mock_user_service.get_access_token.return_value = "jwt_token"

        result = await login(mock_user.email, "password", mock_db)

        assert result.access_token == "jwt_token"
        mock_user_service.get_user.assert_called_once_with(mock_user.email)
        mock_user_service.verify_password.assert_called_once_with(mock_user, "password")
        mock_user_service.get_access_token.assert_called_once_with(mock_user)

    @pytest.mark.parametrize(
        "error_scenario,side_effect",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com")),
            ("invalid_password", user_errors.InvalidPasswordError()),
        ],
        ids=["user_not_found", "invalid_password"]
    )
    async def test_login_errors(
        self,
        mock_db,
        mock_user_service,
        mock_user,
        error_scenario,
        side_effect,
    ):
        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user
            mock_user_service.verify_password.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            await login("user@test.com", "password", mock_db)

        assert exc_info.value.status_code == 401

    async def test_change_password_success(
        self,
        mock_db,
        mock_user_service,
        mock_user,
    ):
        mock_user_service.get_user.return_value = mock_user

        result = await change_password(mock_user.email, "old_pass", "new_pass123!@#", mock_db)

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with(mock_user.email)
        mock_user_service.verify_password.assert_called_once_with(mock_user, "old_pass")
        mock_user_service.validate_password_length.assert_called_once_with("new_pass123!@#")
        mock_user_service.change_password.assert_called_once_with(mock_user, "new_pass123!@#")
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
            ("weak_password", user_errors.WeakPasswordError(), 422),
        ],
        ids=["user_not_found", "weak_password"]
    )
    async def test_change_password_errors(
        self,
        mock_db,
        mock_user_service,
        mock_user,
        error_scenario,
        side_effect,
        expected_status,
    ):
        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user
            mock_user_service.verify_password.return_value = None
            mock_user_service.validate_password_length.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            await change_password("user@test.com", "old_pass", "new_pass", mock_db)

        assert exc_info.value.status_code == expected_status

    async def test_get_my_instructor_courses_success(
        self,
        mock_db,
        mock_user_service,
        mock_get_current_user,
        mock_user,
    ):
        mock_get_current_user.return_value = mock_user.email
        mock_user_service.get_user.return_value = mock_user

        mock_courses = [MagicMock(), MagicMock()]
        mock_user_service.get_instructor_courses.return_value = mock_courses

        with patch("src.routers.users.CourseID.model_validate") as mock_validate:
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_my_instructor_courses(mock_db, mock_user.email)

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with(mock_user.email)
        mock_user_service.get_instructor_courses.assert_called_once_with(mock_user)
        assert mock_validate.call_count == 2

    async def test_get_my_instructor_courses_user_not_found(
        self,
        mock_db,
        mock_user_service,
        mock_get_current_user,
    ):
        mock_get_current_user.return_value = "user@test.com"
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_my_instructor_courses(mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    async def test_remove_user_success(
        self,
        mock_db,
        mock_user_service,
        mock_get_current_user,
        mock_user,
    ):
        mock_get_current_user.return_value = mock_user.email
        mock_user_service.get_user.return_value = mock_user

        result = await remove_user(mock_db, mock_user.email)

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with(mock_user.email)
        mock_user_service.delete_user.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401),
            ("last_admin", admin_errors.DeleteLastAdminError(), 403),
        ],
        ids=["user_not_found", "last_admin"]
    )
    async def test_remove_user_errors(
        self,
        mock_db,
        mock_user_service,
        mock_get_current_user,
        mock_user,
        error_scenario,
        side_effect,
        expected_status,
    ):
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_user
            mock_user_service.delete_user.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            await remove_user(mock_db, "user@test.com")

        assert exc_info.value.status_code == expected_status
        if error_scenario != "user_not_found":
            mock_user_service.get_user.assert_called_once()
