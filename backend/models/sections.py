from pydantic import BaseModel, ConfigDict
from typing import Literal

class SectionID(BaseModel):
    section_id: int


class Section(SectionID):
    title: str
    order: int


class CoursePost(BaseModel):
    course_id: str
    post_id: int
    section_id: int
    creation_time: str
    type: Literal["material", "assignment"]
    author: str
    title: str
    model_config = ConfigDict(from_attributes=True)
