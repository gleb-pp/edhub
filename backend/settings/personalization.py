from pydantic_settings import BaseSettings, SettingsConfigDict


class PersonalizationSettings(BaseSettings):
    """Personalization settings."""

    emoji_count: int = 80

    model_config = SettingsConfigDict()


personalization_settings = PersonalizationSettings()
