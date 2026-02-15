from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CourseID(BaseModel):
    course_id: str
    model_config = ConfigDict(from_attributes=True)


class Course(CourseID):
    title: str
    organization: str | None
    instructor: str
    creation_time: datetime
