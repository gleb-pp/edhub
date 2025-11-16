from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    """Admin settings."""

    default_admin_account_email: str = 'admin'
    default_admin_account_name: str = 'admin'
    default_admin_account_password: str = 'admin'

    model_config = SettingsConfigDict()


admin_settings = AdminSettings()
