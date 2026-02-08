from secrets import token_hex

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """Authorization settings."""

    jwt_secret_key: str = token_hex(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    model_config = SettingsConfigDict(env_prefix="auth_")


auth_settings = AuthSettings()
