from pydantic_settings import BaseSettings, SettingsConfigDict


class SubmissionSettings(BaseSettings):
    """Submission info settings."""

    submission_text_min_length: int = 3
    submission_text_max_length: int = 10000

    grade_comment_min_lenght: int = 3
    grade_comment_max_lenght: int = 10000

    model_config = SettingsConfigDict()


submission_settings = SubmissionSettings()
