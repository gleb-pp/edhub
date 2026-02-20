from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CoursePost(BaseModel):
    """Pydantic model for representing a post in a course section feed."""

    course_id: str
    post_id: int
    section_id: int
    creation_time: datetime
    type: Literal["material", "assignment"]
    author: str | None
    title: str
    model_config = ConfigDict(from_attributes=True)


class SectionID(BaseModel):
    """Pydantic model for basic identification of a course section."""

    course_id: str
    section_id: int
    model_config = ConfigDict(from_attributes=True)


class Section(SectionID):
    """Pydantic model for course sections full information."""

    title: str
    section_order: int
    feed: list[CoursePost] = Field(default_factory=list)
