from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaterialID(BaseModel):
    """Pydantic model for basic identification of a course material."""

    course_id: str
    material_id: int
    section_id: int
    model_config = ConfigDict(from_attributes=True)


class Material(MaterialID):
    """Pydantic model for course materials full information."""

    creation_time: datetime
    title: str
    description: str
    author: str | None


class MaterialAttachmentMetadata(BaseModel):
    """Pydantic model for metadata of files attached to course materials."""

    course_id: str
    material_id: int
    file_id: str
    filename: str
    upload_time: datetime
    model_config = ConfigDict(from_attributes=True)
