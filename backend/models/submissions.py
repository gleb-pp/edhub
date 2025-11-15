from pydantic import BaseModel

class Submission(BaseModel):
    course_id: str
    assignment_id: int
    email: str
    timeadded: str
    timemodified: str
    submission_text: str


class SubmissionAttachmentMetadata(BaseModel):
    course_id: str
    assignment_id: int
    student_email: str
    file_id: str
    filename: str
    upload_time: str
