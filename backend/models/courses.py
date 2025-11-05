from pydantic import BaseModel

class CourseID(BaseModel):
    course_id: str


class Course(CourseID):
    title: str
    instructor_email: str
    instructor_name: str
    organization: str | None
    creation_time: str
    emoji_id: int | None
