from pydantic import BaseModel, ConfigDict
from typing import Literal
from datetime import datetime

class SectionID(BaseModel):
    course_id: int
    section_id: int
    model_config = ConfigDict(from_attributes=True)


class Section(SectionID):
    title: str
    order: int


class CoursePost(BaseModel):
    course_id: str
    post_id: int
    section_id: int
    creation_time: datetime
    type: Literal["material", "assignment"]
    author: str
    title: str
    model_config = ConfigDict(from_attributes=True)
