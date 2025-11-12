class UserError(Exception):
    """Base exception for user-related errors."""


class EmailFormatError(UserError):
    """Exception raised for invalid email format."""

    def __init__(self) -> None:
        super().__init__("Invalid email format.")


class NameFormatError(UserError):
    """Exception raised for invalid user name format."""

    def __init__(self) -> None:
        super().__init__("Invalid user name format.")


class WeakPasswordError(UserError):
    """Exception raised for weak passwords."""

    def __init__(self) -> None:
        super().__init__("Password is too weak.")


class UserExistsError(UserError):
    """Exception raised when trying to create a user that already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(f"User {email} already exists.")


class UserNotFoundError(UserError):
    """Exception raised when a user is not found."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"User {email} does not exist.")


class InvalidPasswordError(UserError):
    """Exception raised for invalid password."""

    def __init__(self) -> None:
        super().__init__("Invalid password.")


# class InvalidTokenError(UserError):
#     """Exception raised for invalid authentication token."""

#     def __init__(self) -> None:
#         super().__init__("Invalid authentication token.")


class AdminRoleRequiredError(UserError):
    """Exception raised when the user does not have the admin role."""

    def __init__(self, user_email: str) -> None:
        super().__init__(f"User {user_email} is not the admin.")


class DeleteLastAdminError(UserError):
    """Exception raised when trying to delete the last administrator."""

    def __init__(self) -> None:
        super().__init__(f"Cannot remove user the only administrator.")
