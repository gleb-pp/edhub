from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssignmentGrade(BaseModel):
    """Pydantic model for representing a grade for a course assignment."""

    course_id: str
    assignment_id: int
    student_email: str
    grade: int
    comment: str | None
    teacher_email: str | None
    time_graded: datetime
    model_config = ConfigDict(from_attributes=True)
