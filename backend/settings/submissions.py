from pydantic_settings import BaseSettings, SettingsConfigDict


class SubmissionSettings(BaseSettings):
    """Submission info settings."""

    submission_text_min_length = 3
    submission_text_max_length = 10000

    grade_comment_min_lenght = 3
    grade_comment_max_lenght = 10000

    model_config = SettingsConfigDict()


submission_settings = SubmissionSettings()
