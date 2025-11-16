from pydantic_settings import BaseSettings, SettingsConfigDict


class SectionSettings(BaseSettings):
    """Section info settings."""

    name_min_lenght: int = 3
    name_max_lenght: int = 80

    model_config = SettingsConfigDict(env_prefix="assignment_")


section_settings = SectionSettings()
