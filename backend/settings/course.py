from pydantic_settings import BaseSettings, SettingsConfigDict


class CourseSettings(BaseSettings):
    """Course info settings."""

    emoji_count: int = 80

    course_name_min_lenght: int = 3
    course_name_max_lenght: int = 80
    course_organization_min_lenght: int = 3
    course_organization_max_lenght: int = 80

    filename_max_lenght: int = 80

    model_config = SettingsConfigDict()


course_settings = CourseSettings()
