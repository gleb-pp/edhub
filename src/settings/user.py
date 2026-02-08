from pydantic_settings import BaseSettings, SettingsConfigDict


class UserSettings(BaseSettings):
    """User info settings."""

    max_email_length: int = 254
    max_email_local_part: int = 64
    max_user_name_length: int = 80
    min_user_name_length: int = 1
    pwd_min_length: int = 8

    model_config = SettingsConfigDict(env_prefix="user_")


user_settings = UserSettings()
