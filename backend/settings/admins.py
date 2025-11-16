from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    """Admin settings."""

    default_admin_account_email = 'admin'
    default_admin_account_name = 'admin'
    default_admin_account_password = 'admin'

    model_config = SettingsConfigDict()


admin_settings = AdminSettings()
