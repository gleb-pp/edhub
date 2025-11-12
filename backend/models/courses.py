from pydantic import BaseModel

class CourseID(BaseModel):
    course_id: str


class Course(CourseID):
    title: str
    organization: str | None
    instructor: str
    creation_time: str
