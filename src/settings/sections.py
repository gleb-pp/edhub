from pydantic_settings import BaseSettings, SettingsConfigDict


class SectionSettings(BaseSettings):
    """Section info settings."""

    name_min_length: int = 3
    name_max_length: int = 80

    model_config = SettingsConfigDict(env_prefix="section_")


section_settings = SectionSettings()
