from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

import src.exceptions.admins as admin_errors
from src.exceptions import users as user_errors
from src.repo import Course, User
from src.services import UserService
from src.settings.user import user_settings


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock(spec=Session)

@pytest.fixture
def service(mock_db) -> UserService:
    return UserService(mock_db)

@pytest.fixture
def mock_user() -> MagicMock:
    user = MagicMock(spec=User)
    user.email = "user@test.com"
    user.password_hash = "hashed_pwd"
    user.isadmin = False
    return user

@pytest.fixture
def mock_course() -> MagicMock:
    course = MagicMock(spec=Course)
    course.course_id = 1
    return course


class TestUserService:

    def test_validate_user_email_success(self, service) -> None:
        valid_emails = [
            "user@example.com",
            "user.name@example.co.uk",
            "user+tag@example.org",
            "user123@example.com",
        ]
        for email in valid_emails:
            service.validate_user_email(email)

    def test_validate_user_email_invalid_format(self, service) -> None:
        invalid_emails = [
            "user@.com",
            "@example.com",
            "user@example",
            "user@example.",
            "user@@example.com",
            "user@exam ple.com",
        ]
        for email in invalid_emails:
            with pytest.raises(user_errors.EmailFormatError):
                service.validate_user_email(email)

    def test_validate_user_email_too_long(self, service) -> None:
        local_part = "a" * (user_settings.max_email_local_part + 1)
        email = f"{local_part}@example.com"
        with pytest.raises(user_errors.EmailFormatError):
            service.validate_user_email(email)

    def test_validate_user_email_double_dot(self, service) -> None:
        with pytest.raises(user_errors.EmailFormatError):
            service.validate_user_email("user..name@example.com")

    def test_validate_user_name_success(self, service) -> None:
        valid_names = [
            "John Doe",
            "Анна Петрова",
            "John_Doe",
            "John123",
            "J",
        ]
        for name in valid_names:
            service.validate_user_name(name)

    def test_validate_user_name_too_short(self, service) -> None:
        with pytest.raises(user_errors.NameFormatError):
            service.validate_user_name("")

    def test_validate_user_name_too_long(self, service) -> None:
        long_name = "a" * (user_settings.max_user_name_length + 1)
        with pytest.raises(user_errors.NameFormatError):
            service.validate_user_name(long_name)

    def test_validate_user_name_starts_with_digit(self, service) -> None:
        with pytest.raises(user_errors.NameFormatError):
            service.validate_user_name("123John")

    def test_validate_user_name_invalid_chars(self, service) -> None:
        with pytest.raises(user_errors.NameFormatError):
            service.validate_user_name("John@Doe")

    def test_validate_password_length_success(self, service) -> None:
        valid_passwords = [
            "Pass123!@#",
            "SecurePwd123$",
            "Aa1!Bb2@",
        ]
        for pwd in valid_passwords:
            service.validate_password_length(pwd)

    def test_validate_password_length_too_short(self, service) -> None:
        with pytest.raises(user_errors.WeakPasswordError):
            service.validate_password_length("A1!")

    def test_validate_password_length_no_digit(self, service) -> None:
        with pytest.raises(user_errors.WeakPasswordError):
            service.validate_password_length("Password!@#")

    def test_validate_password_length_no_letter(self, service) -> None:
        with pytest.raises(user_errors.WeakPasswordError):
            service.validate_password_length("123456!@#")

    def test_validate_password_length_no_special(self, service) -> None:
        with pytest.raises(user_errors.WeakPasswordError):
            service.validate_password_length("Password123")

    @patch("src.services.users.hash_password", return_value="hashed_pwd")
    @patch.object(UserService.logger, "info")
    @patch.object(UserService.logger, "warning")
    def test_create_user_success(self, mock_warning, mock_info, mock_hash, service, mock_db) -> None:
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.create_user("user@test.com", "John Doe", "Pass123!@#")

        assert isinstance(result, User)
        assert result.email == "user@test.com"
        assert result.name == "John Doe"
        assert result.password_hash == "hashed_pwd"

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_info.assert_called_once()
        mock_warning.assert_not_called()
        mock_hash.assert_called_once_with("Pass123!@#")

    @patch.object(UserService.logger, "warning")
    def test_create_user_already_exists(self, mock_logger, service, mock_db) -> None:
        existing_user = MagicMock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user

        with pytest.raises(user_errors.UserExistsError) as exc_info:
            service.create_user("existing@test.com", "John Doe", "Pass123!@#")

        assert "existing@test.com" in str(exc_info.value)
        mock_logger.assert_called_once()
        mock_db.add.assert_not_called()

    @patch("src.services.users.jwt.encode", return_value="jwt_token")
    def test_get_access_token(self, mock_jwt_encode, service, mock_user) -> None:
        result = service.get_access_token(mock_user)

        assert result == "jwt_token"
        mock_jwt_encode.assert_called_once()

    def test_get_user_success(self, service, mock_db) -> None:
        expected_user = MagicMock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = expected_user

        result = service.get_user("user@test.com")
        assert result == expected_user
        mock_db.query.assert_called_once_with(User)
        mock_db.query.return_value.filter.assert_called_once()

    @patch.object(UserService.logger, "warning")
    def test_get_user_not_found(self, mock_logger, service, mock_db) -> None:
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(user_errors.UserNotFoundError) as exc_info:
            service.get_user("nonexistent@test.com")

        assert "nonexistent@test.com" in str(exc_info.value)
        mock_logger.assert_called_once()

    @patch("src.services.users.verify_password")
    @patch.object(UserService.logger, "warning")
    def test_verify_password_success(self, mock_warning, mock_verify, service, mock_user) -> None:
        mock_verify.return_value = True
        service.verify_password(mock_user, "correct_password")
        mock_verify.assert_called_once_with("correct_password", "hashed_pwd")
        mock_warning.assert_not_called()

    @patch("src.services.users.verify_password")
    @patch.object(UserService.logger, "warning")
    def test_verify_password_invalid(self, mock_warning, mock_verify, service, mock_user) -> None:
        mock_verify.return_value = False
        with pytest.raises(user_errors.InvalidPasswordError):
            service.verify_password(mock_user, "wrong_password")
        mock_warning.assert_called_once()

    @patch("src.services.users.hash_password", return_value="new_hashed_pwd")
    @patch.object(UserService.logger, "info")
    def test_change_password_success(self, mock_logger, mock_hash, service, mock_user, mock_db) -> None:
        service.change_password(mock_user, "new_password")

        assert mock_user.password_hash == "new_hashed_pwd"
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()
        mock_hash.assert_called_once_with("new_password")

    def test_get_instructor_courses(self, service, mock_user, mock_db) -> None:
        expected_courses = [MagicMock(spec=Course), MagicMock(spec=Course)]
        mock_db.query.return_value.filter.return_value.all.return_value = expected_courses

        result = service.get_instructor_courses(mock_user)
        assert result == expected_courses
        mock_db.query.assert_called_once_with(Course)
        mock_db.query.return_value.filter.assert_called_once()

    @patch.object(UserService.logger, "info")
    @patch.object(UserService.logger, "warning")
    def test_delete_user_success(self, mock_warning, mock_info, service, mock_user, mock_db) -> None:
        mock_admin = MagicMock(spec=User)
        mock_admin.email = "admin@test.com"
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_admin]

        service.delete_user(mock_user)

        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.flush.assert_called_once()
        mock_info.assert_called_once()
        mock_warning.assert_not_called()

    @patch.object(UserService.logger, "warning")
    def test_delete_user_last_admin(self, mock_logger, service, mock_user, mock_db) -> None:
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_user]

        with pytest.raises(admin_errors.DeleteLastAdminError):
            service.delete_user(mock_user)

        mock_logger.assert_called_once()
        mock_db.delete.assert_not_called()

    @patch.object(UserService.logger, "info")
    def test_give_admin_permissions(self, mock_logger, service, mock_user, mock_db) -> None:
        service.give_admin_permissions(mock_user)
        assert mock_user.isadmin is True
        mock_db.flush.assert_called_once()
        mock_logger.assert_called_once()

    def test_get_all_users(self, service, mock_db) -> None:
        expected_users = [MagicMock(spec=User), MagicMock(spec=User)]
        mock_db.query.return_value.all.return_value = expected_users

        result = service.get_all_users()
        assert result == expected_users
        mock_db.query.assert_called_once_with(User)

    def test_get_all_users_empty(self, service, mock_db) -> None:
        mock_db.query.return_value.all.return_value = []

        result = service.get_all_users()
        assert result == []

    def test_get_admins(self, service, mock_db) -> None:
        expected_admins = [MagicMock(spec=User), MagicMock(spec=User)]
        mock_db.query.return_value.filter.return_value.all.return_value = expected_admins

        result = service.get_admins()
        assert result == expected_admins
        mock_db.query.assert_called_once_with(User)
        mock_db.query.return_value.filter.assert_called_once_with(User.isadmin)

    def test_get_admins_empty(self, service, mock_db) -> None:
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service.get_admins()
        assert result == []
