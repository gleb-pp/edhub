from repo.users import User
import exceptions.admins as admin_errors


class AdminPolicy:
    """Policy class for admin-related actions."""

    @staticmethod
    def assert_user_is_admin(user: User) -> None:
        """Check whether the user with provided email has admin role."""
        if not user.is_admin:
            raise admin_errors.AdminRoleRequiredError(user.email)
