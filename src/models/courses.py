from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CourseID(BaseModel):
    """Pydantic model for basic identification of a course."""

    course_id: str
    model_config = ConfigDict(from_attributes=True)


class Course(CourseID):
    """Pydantic model for course full information."""

    title: str
    organization: str | None
    instructor: str
    creation_time: datetime
