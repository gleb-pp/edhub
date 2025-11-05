from pydantic import BaseModel

class MaterialID(BaseModel):
    course_id: str
    material_id: int
    section_id: int


class Material(MaterialID):
    creation_time: str
    title: str
    description: str
    author: str | None


class MaterialAttachmentMetadata(BaseModel):
    course_id: str
    material_id: int
    file_id: str
    filename: str
    upload_time: str