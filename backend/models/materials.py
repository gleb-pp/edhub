from pydantic import BaseModel, ConfigDict
from datetime import datetime


class MaterialID(BaseModel):
    course_id: str
    material_id: int
    section_id: int
    model_config = ConfigDict(from_attributes=True)


class Material(MaterialID):
    creation_time: datetime
    title: str
    description: str
    author: str | None


# TODO: model_config?
class MaterialAttachmentMetadata(BaseModel):
    course_id: str
    material_id: int
    file_id: str
    filename: str
    upload_time: datetime
