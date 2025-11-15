from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    email: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class CourseRole(BaseModel):
    is_instructor: bool
    is_teacher: bool
    is_student: bool
    is_parent: bool
    is_admin: bool


class AccessToken(BaseModel):
    access_token: str
