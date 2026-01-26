from fastapi import APIRouter, Query, Depends, HTTPException
from auth import get_current_user
from models.common import Success
from models.sections import CoursePost, SectionID, Section
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
from services import (
    UserService,
    CourseService,
    SectionService,
    MaterialService,
    AssignmentService,
)
from policies import CoursePolicy, TeacherPolicy
from exceptions import (
    users as user_errors,
    courses as course_errors,
    sections as section_errors,
    teachers as teacher_errors,
)
from settings.sections import section_settings

router = APIRouter(
    tags=["Course Sections"],
    prefix="/{course_id}/sections",
)


@router.get("/")
async def get_course_sections(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> list[Section]:
    """
    Get the list of course sections.

    Each section is represented as (section_id, title, order).

    Rows are ordered by order.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    section_service = SectionService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if not user.isadmin:
            CoursePolicy.assert_course_access(user, course, db)
        sections = section_service.get_course_sections(course)
        return [Section.model_validate(sec) for sec in sections]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{section_id}")
async def get_section_feed(
    course_id: str,
    section_id: int,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> list[CoursePost]:
    """
    Get the list of materials and assignments for the provided section_id in the provided course_id.

    Each element is represented as (course_id, post_id, section_id, creation_time, type, author, title).

    Type can be 'material' or 'assignment'.

    Elements are ordered by by creation_date, old posts go first.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    section_service = SectionService(db)
    material_service = MaterialService(db)
    assignment_service = AssignmentService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if not user.isadmin:
            CoursePolicy.assert_course_access(user, course, db)
        section = section_service.get_section(course, section_id)
        materials = material_service.get_section_materials(section)
        materials_posts = [
            {
                **mat.__dict__,
                "type": "material",
                "post_id": mat.material_id,
            }
            for mat in materials
        ]
        assignments = assignment_service.get_section_assignments(section)
        assignments_posts = [
            {
                **ass.__dict__,
                "type": "assignment",
                "post_id": ass.assignment_id,
            }
            for ass in assignments
        ]
        course_feed = sorted(
            materials_posts + assignments_posts, key=lambda p: p["creation_time"]
        )
        return [CoursePost.model_validate(post) for post in course_feed]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except section_errors.SectionNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/")
async def create_section(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    title: str = Query(
        ...,
        min_length=section_settings.name_min_lenght,
        max_length=section_settings.name_max_lenght,
        pattern=r"^[\p{L}0-9_ ]+$",
        description=f"Section title can contain only letters, digits, spaces, and underscores, {section_settings.name_min_lenght}-{section_settings.name_max_lenght} symbols",
    ),
    teacher_email: str = Depends(get_current_user),
) -> SectionID:
    """
    Create the course section with provided title within the course with provided course_id.

    Title contain only letters, digits, spaces, and underscores.

    Title must contains from 3 to 80 symbols.

    Teacher OR Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    section_service = SectionService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        section = section_service.create_section(title, course)
        db.commit()
        return SectionID.model_validate(section)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.put("/change_section_order")
async def change_section_order(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    new_order: list[int] = Query(...),
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Change the order of sections within the course with provided course_id.

    The list of section_ids should be passed as a new_order parameter.

    Teacher OR Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    section_service = SectionService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        section_service.change_section_order(course, new_order)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        section_errors.SectionNotFoundError,
        section_errors.IncorrectSectionOrderError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.delete("/remove_section")
async def remove_section(
    course_id: str,
    section_id: int,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Remove the section with provided section_id from the course with provided course_id.

    All the materials and assignments within the removed section will be also removed.

    Impossible to remove the last section from the course.

    Teacher OR Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    section_service = SectionService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        section = section_service.get_section(course, section_id)
        section_service.remove_section(section)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        section_errors.SectionNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except section_errors.LastSectionDeleteError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
