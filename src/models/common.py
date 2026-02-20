from pydantic import BaseModel


class Success(BaseModel):
    """Pydantic model for API responses indicating success or failure."""

    success: bool
