from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssignmentID(BaseModel):
    """Pydantic model for basic identification of a course assignment."""

    course_id: str
    assignment_id: int
    section_id: int
    model_config = ConfigDict(from_attributes=True)


class Assignment(AssignmentID):
    """Pydantic model for course assignments full information."""

    creation_time: datetime
    title: str
    description: str
    author: str | None


class AssignmentAttachmentMetadata(BaseModel):
    """Pydantic model for metadata of files attached to course assignments."""

    course_id: str
    assignment_id: int
    file_id: str
    filename: str
    upload_time: datetime
    model_config = ConfigDict(from_attributes=True)
