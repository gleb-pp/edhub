from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """Pydantic model for representing a user in the system."""

    email: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class CourseRole(BaseModel):
    """Pydantic model for representing a user's role in a course."""

    is_instructor: bool
    is_teacher: bool
    is_student: bool
    is_parent: bool
    is_admin: bool


class AccessToken(BaseModel):
    """Pydantic model for representing an access token for a user."""

    access_token: str
