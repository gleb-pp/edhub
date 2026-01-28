from regex import match, search
from settings.user import user_settings
from exceptions import users as user_errors
import exceptions.admins as admin_errors
from sqlalchemy.orm import Session
from repo.users import User
from repo.courses import Course
from auth import pwd_hasher
from settings.auth import auth_settings
from jose import jwt
from datetime import datetime, timedelta, timezone
import logging


class UserService:
    """Service class for user-related operations."""

    logger = logging.getLogger(__name__)

    def __init__(self, db: Session):
        self.db = db

    def validate_user_email(self, email: str) -> None:
        """Validate the format of the provided user email."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not (
            match(pattern, email)
            and len(email) <= user_settings.max_email_lenght
            and ".." not in email
            and len(email.split("@")[0]) <= user_settings.max_email_local_part
        ):
            raise user_errors.EmailFormatError

    def validate_user_name(self, name: str) -> None:
        """Validate the format of the provided user name."""
        pattern = r"^[\p{L}0-9_ ]+$"
        name = name.strip()
        if not (
            match(pattern, name)
            and user_settings.min_user_name_lenght
            <= len(name)
            <= user_settings.max_user_name_lenght
            and not (name[0].isdigit())
        ):
            raise user_errors.NameFormatError

    def validate_password_lenght(self, password: str) -> None:
        """Validate the length of the provided user password."""
        if not (
            len(password) >= user_settings.pwd_min_lenght
            and search(r"\d", password)
            and search(r"\p{L}", password)
            and search(r"[^\p{L}\p{N}\s]", password)
        ):
            raise user_errors.WeakPasswordError

    def create_user(self, email: str, name: str, password: str) -> User:
        """Create a new user with provided email, name, and password."""
        # checking whether such user exists
        if self.db.query(User).filter(User.email == email).first() is not None:
            self.logger.warning(
                f"Attempt to create a user with existing email: {email}"
            )
            raise user_errors.UserExistsError(email)

        # hashing password
        hashed_password = pwd_hasher.hash(password)
        user = User(email=email, name=name, password_hash=hashed_password)
        self.db.add(user)
        self.db.flush()
        self.logger.info(f"User created with email {email} and name {name}")
        return user

    def get_access_token(self, user: User) -> str:
        """Get JWT access token for user with provided email and password."""
        # giving access token
        data = {
            "email": user.email,
            "exp": datetime.now(tz=timezone.utc)
            + timedelta(minutes=auth_settings.access_token_expire_minutes),
        }
        return jwt.encode(
            data, auth_settings.jwt_secret_key, algorithm=auth_settings.algorithm
        )

    def get_user(self, email: str) -> User:
        """Check whether a user with provided email exists in the system."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            self.logger.warning(f"Attempt to get non-existent user with email: {email}")
            raise user_errors.UserNotFoundError(email)
        return user

    def verify_password(self, user: User, password: str) -> None:
        """Verify that the provided password is correct for the user with provided email."""
        if not pwd_hasher.verify(password, user.password_hash):
            self.logger.warning(
                f"Invalid password attempt for user with email: {user.email}"
            )
            raise user_errors.InvalidPasswordError

    def change_password(self, user: User, new_password: str) -> None:
        """Change the user password to a new one."""
        self.logger.info(f"Changing password for user with email: {user.email}")
        hashed_password = pwd_hasher.hash(new_password)
        user.password_hash = hashed_password
        self.db.flush()

    def get_instructor_courses(self, user: User) -> list[Course]:
        """Change the list of courses with the provided user as an instructor."""
        return self.db.query(Course).filter(Course.instructor == user.email).all()

    def delete_user(self, user: User) -> None:
        """Delete user from the system."""
        admins = self.get_admins()
        if len(admins) == 1 and admins[0].email == user.email:
            self.logger.warning("Attempt to delete the last admin user.")
            raise admin_errors.DeleteLastAdminError
        self.db.delete(user)
        self.db.flush()
        self.logger.info(f"Deleting user with email: {user.email}")

    def give_admin_permissions(self, user: User) -> None:
        """Change the user password to a new one."""
        user.isadmin = True
        self.db.flush()
        self.logger.info(f"Granting admin permissions to user with email: {user.email}")

    def get_all_users(self) -> list[User]:
        """Get the list of all users."""
        return self.db.query(User).all()

    def get_admins(self) -> list[User]:
        """Get the list of all administrators."""
        return self.db.query(User).filter(User.is_admin).all()
