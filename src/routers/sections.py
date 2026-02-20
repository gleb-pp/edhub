from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.auth import get_current_user
from src.db import get_db
from src.exceptions import courses as course_errors
from src.exceptions import sections as section_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.models.sections import CoursePost, Section, SectionID
from src.policies import CoursePolicy, TeacherPolicy
from src.services import (
    AssignmentService,
    CourseService,
    MaterialService,
    SectionService,
    UserService,
)
from src.settings.sections import section_settings

router = APIRouter(
    tags=["Course Sections"],
    prefix="/courses/{course_id}",
)


@router.get("/sections")
async def get_course_sections(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: Annotated[str, Depends(get_current_user)],
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
    except course_errors.ParticipantRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/feed")
async def get_course_feed(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: Annotated[str, Depends(get_current_user)],
) -> list[Section]:
    """
    Get the list of materials and assignments for the provided section_id in the provided course_id.

    Each element is represented as (course_id, post_id, section_id, creation_time, type, author, title).

    Type can be 'material' or 'assignment'.

    Elements are ordered by creation_time, old posts go first.

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
        sections = section_service.get_course_sections(course)
        course_feed = []
        for sec in sections:
            # collect materials
            materials = material_service.get_section_materials(sec)
            materials_posts = [
                CoursePost(
                    course_id=mat.course_id,
                    section_id=mat.section_id,
                    creation_time=mat.creation_time,
                    author=mat.author,
                    title=mat.title,
                    type="material",
                    post_id=mat.material_id,
                )
                for mat in materials
            ]
            # collect assignments
            assignments = assignment_service.get_section_assignments(sec)
            assignments_posts = [
                CoursePost(
                    course_id=ass.course_id,
                    section_id=ass.section_id,
                    creation_time=ass.creation_time,
                    author=ass.author,
                    title=ass.title,
                    type="assignment",
                    post_id=ass.assignment_id,
                )
                for ass in assignments
            ]
            # costruct the section model
            section_model = Section.model_validate(sec)
            section_model.feed = sorted(
                materials_posts + assignments_posts, key=lambda p: p.creation_time,
            )
            course_feed.append(section_model)
        return course_feed
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except section_errors.SectionNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/sections")
async def create_section(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: Annotated[str, Depends(get_current_user)],
    title: Annotated[str, Query(
        ...,
        min_length=section_settings.name_min_length,
        max_length=section_settings.name_max_length,
        pattern=r"^[\p{L}0-9_ ]+$",
        description=f"Section title can contain only letters, digits, spaces, and underscores, {section_settings.name_min_length}-{section_settings.name_max_length} symbols",
    )],
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
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.put("/sections/order")
async def change_section_order(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    new_order: Annotated[list[int], Query(...)],
    teacher_email: Annotated[str, Depends(get_current_user)],
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
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.delete("/sections/{section_id}")
async def remove_section(
    course_id: str,
    section_id: int,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: Annotated[str, Depends(get_current_user)],
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
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except section_errors.LastSectionDeleteError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
