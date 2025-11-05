from fastapi import APIRouter, Depends, Query, UploadFile, File
from auth import get_current_user, get_db, get_storage_db
from models.common import Success
from models.materials import MaterialID, Material, MaterialAttachmentMetadata
import logic.materials


router = APIRouter(
    prefix="/{course_id}/materials",
    tags=["Materials"],
)


@router.post("/{section_id}")
async def create_material(
    course_id: str,
    section_id: int,
    title: str = Query(
        ...,
        min_length=3,
        max_length=80,
        pattern=r"^[\p{L}0-9_ ]+$",
        description="Title can contain only letters, digits, spaces, and underscores, 3-80 symbols"
    ),
    description: str = Query(
        ...,
        min_length=3,
        max_length=10000,
        description="Description must contain 3-10000 symbols"
    ),
    user_email: str = Depends(get_current_user),
) -> MaterialID:
    """
    Create the material with provided title and description within the section by provided section_id within the course with provided course_id.

    Title can contain only letters, digits, spaces, and underscores.

    Title must contain from 3 to 80 symbols.

    Description must contain from 3 to 10000 symbols.

    Teacher OR Primary Instructor role required.

    Returns the (course_id, material_id, section_id) for the new material in case of success.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.materials.create_material(db_conn, db_cursor, course_id, section_id, title, description, user_email)


@router.delete("/{material_id}")
async def remove_material(
    course_id: str,
    material_id: str,
    user_email: str = Depends(get_current_user)
) -> Success:
    """
    Remove the material by the provided course_id and material_id.

    Teacher OR Primary Instructor role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.materials.remove_material(db_conn, db_cursor, course_id, material_id, user_email)


@router.get("/{material_id}")
async def get_material(
    course_id: str,
    material_id: str,
    user_email: str = Depends(get_current_user)
) -> Material:
    """
    Get the material details by the provided (course_id, material_id).

    Returns course_id, material_id, section_id, creation_time, title, description, and email of the author.

    Author can be NULL if the author deleted their account.

    The format of creation time is TIME_FORMAT.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.materials.get_material(db_cursor, course_id, material_id, user_email)


@router.post("/{material_id}/attachment")
async def create_material_attachment(
    course_id: str,
    material_id: str,
    file: UploadFile = File(...),
    user_email: str = Depends(get_current_user),
) -> MaterialAttachmentMetadata:
    """
    Attach the provided file to provided course material.

    Filename should contain no more than 80 symbols.

    Teacher OR Primary Instructor role required.

    Returns the (course_id, material_id, file_id, filename, upload_time) for the new attachment in case of success.

    The format of upload_time is TIME_FORMAT.
    """
    with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
        return await logic.materials.create_material_attachment(db_conn, db_cursor, storage_db_conn, storage_db_cursor, course_id, material_id, file, user_email)


@router.get("/{material_id}/attachment")
async def get_material_attachments(
    course_id: str,
    material_id: str,
    user_email: str = Depends(get_current_user)
) -> list[MaterialAttachmentMetadata]:
    """
    Get the list of course material attachments by provided course_id, material_id.

    Returns list of attachments metadata (course_id, material_id, file_id, filename, upload_time).

    The format of upload_time is TIME_FORMAT.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.materials.get_material_attachments(db_cursor, course_id, material_id, user_email)


@router.get("/{material_id}/attachment/{file_id}")
async def download_material_attachment(
    course_id: str,
    material_id: str,
    file_id: str,
    user_email: str = Depends(get_current_user)
):
    """
    Download the course material attachment by provided course_id, material_id, file_id.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
        return logic.materials.download_material_attachment(db_cursor, storage_db_cursor, course_id, material_id, file_id, user_email)
