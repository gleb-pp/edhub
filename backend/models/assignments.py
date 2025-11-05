from pydantic import BaseModel


class AssignmentID(BaseModel):
    course_id: str
    assignment_id: int
    section_id: int


class Assignment(AssignmentID):
    creation_time: str
    title: str
    description: str
    author: str | None


class AssignmentAttachmentMetadata(BaseModel):
    course_id: str
    assignment_id: int
    file_id: str
    filename: str
    upload_time: str
