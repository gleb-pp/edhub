from pydantic_settings import BaseSettings, SettingsConfigDict


class SectionSettings(BaseSettings):
    """Section info settings."""

    name_min_lenght = 3
    name_max_lenght = 80

    model_config = SettingsConfigDict(env_prefix="assignment_")


section_settings = SectionSettings()
