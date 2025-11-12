from repo.users import User
import exceptions.users as user_errors


def assert_user_is_admin(user: User) -> None:
    """Check whether the user with provided email has admin role."""
    if not user.is_admin:
        raise user_errors.AdminRoleRequiredError(user.email)
