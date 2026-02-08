from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AssignmentID(BaseModel):
    course_id: str
    assignment_id: int
    section_id: int
    model_config = ConfigDict(from_attributes=True)


class Assignment(AssignmentID):
    creation_time: datetime
    title: str
    description: str
    author: str | None


class AssignmentAttachmentMetadata(BaseModel):
    course_id: str
    assignment_id: int
    file_id: str
    filename: str
    upload_time: datetime
    model_config = ConfigDict(from_attributes=True)
