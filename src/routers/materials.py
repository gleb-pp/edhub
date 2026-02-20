from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.auth import get_current_user
from src.db import get_db
from src.exceptions import courses as course_errors
from src.exceptions import materials as material_errors
from src.exceptions import sections as section_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.models.materials import Material, MaterialID
from src.policies import CoursePolicy, TeacherPolicy
from src.services import CourseService, MaterialService, SectionService, UserService
from src.settings.materials import material_settings

router = APIRouter(
    prefix="/courses/{course_id}",
    tags=["Materials"],
)


@router.post("/sections/{section_id}/materials")
async def create_material(
    course_id: str,
    section_id: int,
    db: Annotated[Session, Depends(get_db)],
    title: Annotated[str, Query(
        ...,
        min_length=material_settings.name_min_length,
        max_length=material_settings.name_max_length,
        pattern=r"^[\p{L}0-9_ ]+$",
        description=f"Title can contain only letters, digits, spaces, and underscores, {material_settings.name_min_length}-{material_settings.name_max_length} symbols",
    )],
    description: Annotated[str, Query(
        ...,
        min_length=material_settings.description_min_length,
        max_length=material_settings.description_max_length,
        description=f"Description must contain {material_settings.description_min_length}-{material_settings.description_max_length} symbols",
    )],
    teacher_email: Annotated[str, Depends(get_current_user)],
) -> MaterialID:
    """
    Create the material with provided title and description within the section by provided section_id within the course with provided course_id.

    Title can contain only letters, digits, spaces, and underscores.

    Title must contain from 3 to 80 symbols.

    Description must contain from 3 to 10000 symbols.

    Teacher OR Primary Instructor role required.

    Returns the (course_id, material_id, section_id) for the new material in case of success.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    section_service = SectionService(db)
    material_service = MaterialService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.is_admin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        section = section_service.get_section(course, section_id)
        material = material_service.create_material(
            section, title, description, teacher,
        )
        db.commit()
        return MaterialID.model_validate(material)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        section_errors.SectionNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.delete("/materials/{material_id}")
async def remove_material(
    course_id: str,
    material_id: int,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: Annotated[str, Depends(get_current_user)],
) -> Success:
    """
    Remove the material by the provided course_id and material_id.

    Teacher OR Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    material_service = MaterialService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.is_admin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        material = material_service.get_material(course, material_id)
        material_service.delete_material(material)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        material_errors.MaterialNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/materials/{material_id}")
async def get_material(
    course_id: str,
    material_id: int,
    db: Annotated[Session, Depends(get_db)],
    user_email: Annotated[str, Depends(get_current_user)],
) -> Material:
    """
    Get the material details by the provided (course_id, material_id).

    Returns course_id, material_id, section_id, creation_time, title, description, and email of the author.

    Author can be NULL if the author deleted their account.

    The format of creation time is TIME_FORMAT.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    material_service = MaterialService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if not user.is_admin:
            CoursePolicy.assert_course_access(user, course, db)
        material = material_service.get_material(course, material_id)
        return Material.model_validate(material)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except material_errors.MaterialNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
