import pytest
from typing import cast
from src.repo.users import User
from src.policies.admin import AdminPolicy
from src.exceptions.admins import AdminRoleRequiredError


class DummyUser:
    def __init__(self, email="a@test.com", is_admin=False):
        self.email = email
        self.is_admin = is_admin


class TestAdminPolicy:

    def test_assert_user_is_admin_success(self):
        user = cast(User, DummyUser(is_admin=True))
        AdminPolicy.assert_user_is_admin(user)

    def test_assert_user_is_admin_fail(self):
        user = cast(User, DummyUser(is_admin=False))
        with pytest.raises(AdminRoleRequiredError):
            AdminPolicy.assert_user_is_admin(user)
