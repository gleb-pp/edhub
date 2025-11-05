from pydantic import BaseModel

class Submission(BaseModel):
    course_id: str
    assignment_id: int
    student_email: str
    student_name: str
    submission_time: str
    last_modification_time: str
    submission_text: str
    grade: int | None
    comment: str | None
    gradedby_email: str | None
    gradedby_name: str | None


class SubmissionAttachmentMetadata(BaseModel):
    course_id: str
    assignment_id: int
    student_email: str
    file_id: str
    filename: str
    upload_time: str
