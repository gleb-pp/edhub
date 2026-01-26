class PersonalizationError(Exception):
    """Base exception for personalization-related errors."""


class IncorrectCoursesOrderError(PersonalizationError):
    """Exception raised when trying to insert incorrect order of courses to change."""

    def __init__(self) -> None:
        super().__init__(
            "New list of courses passed does not match with the original one."
        )
