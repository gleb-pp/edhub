from pydantic_settings import BaseSettings, SettingsConfigDict


class UserSettings(BaseSettings):
    """User info settings."""

    max_email_lenght: int = 254
    max_email_local_part: int = 64
    max_user_name_lenght: int = 80
    min_user_name_lenght: int = 1
    pwd_min_lenght: int = 8

    model_config = SettingsConfigDict(env_prefix="user_")


user_settings = UserSettings()
