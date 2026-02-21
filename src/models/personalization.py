from pydantic import BaseModel


class EmojiID(BaseModel):
    """Pydantic model for identifying a course emoji by its ID."""

    emoji_id: int | None
