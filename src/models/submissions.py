from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Submission(BaseModel):
    course_id: str
    assignment_id: int
    email: str
    timeadded: datetime
    timemodified: datetime
    submission_text: str
    model_config = ConfigDict(from_attributes=True)


class SubmissionAttachmentMetadata(BaseModel):
    course_id: str
    assignment_id: int
    student_email: str
    file_id: str
    filename: str
    upload_time: datetime
    model_config = ConfigDict(from_attributes=True)
