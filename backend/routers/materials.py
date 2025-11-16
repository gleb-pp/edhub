from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from auth import get_current_user
from models.common import Success
from models.materials import MaterialID, Material, MaterialAttachmentMetadata
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
import logic.users as user_logic
import logic.courses as course_logic
import logic.sections as section_logic
import exceptions.users as user_errors
import exceptions.courses as course_errors
import exceptions.sections as section_errors
import logic.teachers as teacher_logic
import exceptions.teachers as teacher_errors
import logic.materials as material_logic
import exceptions.materials as material_errors
from settings.materials import material_settings


router = APIRouter(
    prefix="/{course_id}/materials",
    tags=["Materials"],
)


@router.post("/{section_id}")
async def create_material(
    course_id: str,
    section_id: int,
    db: Annotated[Session, Depends(get_db)],
    title: str = Query(
        ...,
        min_length=material_settings.name_min_lenght,
        max_length=material_settings.name_max_lenght,
        pattern=r"^[\p{L}0-9_ ]+$",
        description=f"Title can contain only letters, digits, spaces, and underscores, {material_settings.name_min_lenght}-{material_settings.name_max_lenght} symbols"
    ),
    description: str = Query(
        ...,
        min_length=material_settings.description_min_lenght,
        max_length=material_settings.description_max_lenght,
        description=f"Description must contain {material_settings.description_min_lenght}-{material_settings.description_max_lenght} symbols"
    ),
    teacher_email: str = Depends(get_current_user),
) -> MaterialID:
    """
    Create the material with provided title and description within the section by provided section_id within the course with provided course_id.

    Title can contain only letters, digits, spaces, and underscores.

    Title must contain from 3 to 80 symbols.

    Description must contain from 3 to 10000 symbols.

    Teacher OR Primary Instructor role required.

    Returns the (course_id, material_id, section_id) for the new material in case of success.
    """
    try:
        teacher = user_logic.get_user(teacher_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_teacher_access(teacher, course, db)
        section = section_logic.get_section(course, section_id, db)
        material = material_logic.create_material(section, title, description, teacher, db)
        db.commit()
        return MaterialID.model_validate(material)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        section_errors.SectionNotFoundError
     ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.delete("/{material_id}")
async def remove_material(
    course_id: str,
    material_id: int,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Remove the material by the provided course_id and material_id.

    Teacher OR Primary Instructor role required.
    """
    try:
        teacher = user_logic.get_user(teacher_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_teacher_access(teacher, course, db)
        material = material_logic.get_material(course, material_id, db)
        material_logic.delete_material(material, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        material_errors.MaterialNotFoundError
     ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/{material_id}")
async def get_material(
    course_id: str,
    material_id: int,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user)
) -> Material:
    """
    Get the material details by the provided (course_id, material_id).

    Returns course_id, material_id, section_id, creation_time, title, description, and email of the author.

    Author can be NULL if the author deleted their account.

    The format of creation time is TIME_FORMAT.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        course_logic.assert_course_access(user, course, db)
        material = material_logic.get_material(course, material_id, db)
        return Material.model_validate(material)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except material_errors.MaterialNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# @router.post("/{material_id}/attachment")
# async def create_material_attachment(
#     course_id: str,
#     material_id: str,
#     file: UploadFile = File(...),
#     user_email: str = Depends(get_current_user),
# ) -> MaterialAttachmentMetadata:
#     """
#     Attach the provided file to provided course material.

#     Filename should contain no more than 80 symbols.

#     Teacher OR Primary Instructor role required.

#     Returns the (course_id, material_id, file_id, filename, upload_time) for the new attachment in case of success.

#     The format of upload_time is TIME_FORMAT.
#     """
#     with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
#         return await logic.materials.create_material_attachment(db_conn, db_cursor, storage_db_conn, storage_db_cursor, course_id, material_id, file, user_email)


# @router.get("/{material_id}/attachment")
# async def get_material_attachments(
#     course_id: str,
#     material_id: str,
#     user_email: str = Depends(get_current_user)
# ) -> list[MaterialAttachmentMetadata]:
#     """
#     Get the list of course material attachments by provided course_id, material_id.

#     Returns list of attachments metadata (course_id, material_id, file_id, filename, upload_time).

#     The format of upload_time is TIME_FORMAT.

#     Course role (Primary Instructor, Teacher, Student, Parent) required.
#     """
#     with get_db() as (db_conn, db_cursor):
#         return logic.materials.get_material_attachments(db_cursor, course_id, material_id, user_email)


# @router.get("/{material_id}/attachment/{file_id}")
# async def download_material_attachment(
#     course_id: str,
#     material_id: str,
#     file_id: str,
#     user_email: str = Depends(get_current_user)
# ):
#     """
#     Download the course material attachment by provided course_id, material_id, file_id.

#     Course role (Primary Instructor, Teacher, Student, Parent) required.
#     """
#     with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
#         return logic.materials.download_material_attachment(db_cursor, storage_db_cursor, course_id, material_id, file_id, user_email)
