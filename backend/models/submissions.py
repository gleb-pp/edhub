from pydantic import BaseModel, ConfigDict
from datetime import datetime


class Submission(BaseModel):
    course_id: str
    assignment_id: int
    email: str
    timeadded: datetime
    timemodified: datetime
    submission_text: str
    model_config = ConfigDict(from_attributes=True)


# TODO: model_config?
class SubmissionAttachmentMetadata(BaseModel):
    course_id: str
    assignment_id: int
    student_email: str
    file_id: str
    filename: str
    upload_time: datetime
