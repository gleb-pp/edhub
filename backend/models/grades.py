from pydantic import BaseModel
from datetime import datetime

class StudentsGrades(BaseModel):
    name: str
    email: str
    grades: list[int | None]


class AssignmentGrade(BaseModel):
    course_id: str
    assignment_id: str
    student_email: str 
    grade: str 
    comment: str | None
    teacher_email: str | None
    time_graded: datetime
