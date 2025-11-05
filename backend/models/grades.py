from pydantic import BaseModel

class StudentsGrades(BaseModel):
    name: str
    email: str
    grades: list[int | None]

class AssignmentGrade(BaseModel):
    assignment_name: str
    assignment_id: int
    grade: int | None
    comment: str | None
    grader_name: str | None
    grader_email: str | None
