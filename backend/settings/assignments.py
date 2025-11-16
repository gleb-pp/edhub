from pydantic_settings import BaseSettings, SettingsConfigDict


class AssignmentSettings(BaseSettings):
    """Assignment info settings."""

    name_min_lenght = 3
    name_max_lenght = 80
    description_min_lenght = 3
    description_max_lenght = 10000

    model_config = SettingsConfigDict(env_prefix="assignment_")


assignment_settings = AssignmentSettings()
