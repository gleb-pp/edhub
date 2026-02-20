from unittest.mock import MagicMock

import pytest

from src.exceptions.admins import AdminRoleRequiredError
from src.policies import AdminPolicy
from src.repo.users import User


class TestAdminPolicy:
    """Tests for the AdminPolicy class."""

    def test_assert_user_is_admin_success(self) -> None:
        """Test that assert_user_is_admin does not raise an error for an admin user."""
        mock_user = MagicMock(spec=User)
        mock_user.is_admin = True

        AdminPolicy.assert_user_is_admin(mock_user)

    def test_assert_user_is_admin_fail(self) -> None:
        """Test that assert_user_is_admin raises an AdminRoleRequiredError for a non-admin user."""
        mock_user = MagicMock(spec=User)
        mock_user.is_admin = False

        with pytest.raises(AdminRoleRequiredError):
            AdminPolicy.assert_user_is_admin(mock_user)
