class AdminError(Exception):
    """Base exception for admin-related errors."""


class AdminRoleRequiredError(AdminError):
    """Exception raised when the user does not have the admin role."""

    def __init__(self, user_email: str) -> None:
        super().__init__(
            f"User {user_email} is not the admin.",
        )


class DeleteLastAdminError(AdminError):
    """Exception raised when trying to delete the last administrator."""

    def __init__(self) -> None:
        super().__init__(
            "Cannot remove the only administrator.",
        )
