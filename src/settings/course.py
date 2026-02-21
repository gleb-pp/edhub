from pydantic_settings import BaseSettings, SettingsConfigDict


class CourseSettings(BaseSettings):
    """Course info settings."""

    emoji_count: int = 80

    name_min_length: int = 3
    name_max_length: int = 80
    organization_min_length: int = 3
    organization_max_length: int = 80

    filename_max_length: int = 80

    model_config = SettingsConfigDict(env_prefix="course_")


course_settings = CourseSettings()
