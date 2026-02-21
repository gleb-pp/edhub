from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    """Admin settings."""

    default_account_email: str = "admin"
    default_account_name: str = "admin"
    default_account_password: str = "admin" # noqa: S105

    model_config = SettingsConfigDict(env_prefix="admin_")


admin_settings = AdminSettings()
