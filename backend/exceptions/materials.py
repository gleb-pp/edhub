class MaterialError(Exception):
    """Base exception for material-related errors."""


class MaterialNotFoundError(MaterialError):
    """Exception raised when a material is not found."""

    def __init__(self, course_id: str, material_id: int) -> None:
        super().__init__(f"Material {material_id} does not exist in the course {course_id}.")
