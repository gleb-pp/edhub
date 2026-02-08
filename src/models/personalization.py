from pydantic import BaseModel


class EmojiID(BaseModel):
    emoji_id: int | None
