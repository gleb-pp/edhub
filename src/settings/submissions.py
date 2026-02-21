from pydantic_settings import BaseSettings, SettingsConfigDict


class SubmissionSettings(BaseSettings):
    """Submission info settings."""

    text_min_length: int = 3
    text_max_length: int = 10000

    grade_comment_min_length: int = 3
    grade_comment_max_length: int = 10000

    model_config = SettingsConfigDict(env_prefix="submission_")


submission_settings = SubmissionSettings()
