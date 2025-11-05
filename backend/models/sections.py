from pydantic import BaseModel

class SectionID(BaseModel):
    section_id: int


class Section(SectionID):
    title: str


class CoursePost(BaseModel):
    course_id: str
    post_id: int | None
    section_id: int
    section_name: str
    section_order: int
    type: str | None
    creation_time: str | None
    author: str | None
