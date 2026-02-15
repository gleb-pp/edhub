from unittest.mock import MagicMock

import pytest

from src.exceptions.admins import AdminRoleRequiredError
from src.policies import AdminPolicy
from src.repo.users import User


class TestAdminPolicy:

    def test_assert_user_is_admin_success(self):
        mock_user = MagicMock(spec=User)
        mock_user.is_admin = True

        AdminPolicy.assert_user_is_admin(mock_user)

    def test_assert_user_is_admin_fail(self):
        mock_user = MagicMock(spec=User)
        mock_user.is_admin = False

        with pytest.raises(AdminRoleRequiredError):
            AdminPolicy.assert_user_is_admin(mock_user)
