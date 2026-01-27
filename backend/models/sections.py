from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime


class CoursePost(BaseModel):
    course_id: str
    post_id: int
    section_id: int
    creation_time: datetime
    type: Literal["material", "assignment"]
    author: str | None
    title: str
    model_config = ConfigDict(from_attributes=True)


class SectionID(BaseModel):
    course_id: int
    section_id: int
    model_config = ConfigDict(from_attributes=True)


class Section(SectionID):
    title: str
    section_order: int
    feed: list[CoursePost] = Field(default_factory=list)
