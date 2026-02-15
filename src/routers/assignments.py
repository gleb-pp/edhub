from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.auth import get_current_user
from src.db import get_db
from src.exceptions import assignments as assignment_errors
from src.exceptions import courses as course_errors
from src.exceptions import sections as section_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.assignments import Assignment, AssignmentID
from src.models.common import Success
from src.policies import CoursePolicy, TeacherPolicy
from src.services import AssignmentService, CourseService, SectionService, UserService
from src.settings.assignments import assignment_settings

router = APIRouter(
    prefix="/courses/{course_id}",
    tags=["Assignments"],
)


@router.post("/sections/{section_id}/assignments")
async def create_assignment(
    course_id: str,
    section_id: int,
    db: Annotated[Session, Depends(get_db)],
    title: str = Query(
        ...,
        min_length=assignment_settings.name_min_lenght,
        max_length=assignment_settings.name_max_lenght,
        pattern=r"^[\p{L}0-9_ ]+$",
        description=f"Title can contain only letters, digits, spaces, and underscores, {assignment_settings.name_min_lenght}-{assignment_settings.name_max_lenght} symbols",
    ),
    description: str = Query(
        ...,
        min_length=assignment_settings.description_min_lenght,
        max_length=assignment_settings.description_max_lenght,
        description=f"Description must contain {assignment_settings.description_min_lenght}-{assignment_settings.description_max_lenght} symbols",
    ),
    teacher_email: str = Depends(get_current_user),
) -> AssignmentID:
    """
    Create the assignment with provided title and description within the section by provided section_id within the course with provided course_id.

    Title can contain only letters, digits, spaces, and underscores.

    Title must contain from 3 to 80 symbols.

    Description must contain from 3 to 10000 symbols.

    Teacher OR Primary Instructor role required.

    Returns the (course_id, assignment_id, section_id) for the new assignment in case of success.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    section_service = SectionService(db)
    assignment_service = AssignmentService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        section = section_service.get_section(course, section_id)
        assignment = assignment_service.create_assignment(
            section, title, description, teacher
        )
        db.commit()
        return AssignmentID.model_validate(assignment)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        section_errors.SectionNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.delete("/assignments/{assignment_id}")
async def remove_assignment(
    course_id: str,
    assignment_id: int,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Remove the assignment by the provided course_id and assignment_id.

    Teacher OR Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    assignment_service = AssignmentService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        assignment = assignment_service.get_assignment(course, assignment_id)
        assignment_service.delete_assignment(assignment)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        assignment_errors.AssignmentNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/assignments/{assignment_id}")
async def get_assignment(
    course_id: str,
    assignment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> Assignment:
    """
    Get the assignment details by the provided (course_id, assignment_id).

    Returns course_id, assignment_id, section_id, creation_time, title, description, and email of the author.

    Author can be NULL if the author deleted their account.

    The format of creation time is TIME_FORMAT.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    assignment_service = AssignmentService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if not user.isadmin:
            CoursePolicy.assert_course_access(user, course, db)
        assignment = assignment_service.get_assignment(course, assignment_id)
        return Assignment.model_validate(assignment)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except assignment_errors.AssignmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/assignments")
async def get_course_assignments(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> list[Assignment]:
    """
    Get the list of course assignments by the provided course_id.

    For each assignment, it returns course_id, assignment_id, section_id, creation_time, title, description, and email of the author.

    Author can be NULL if the author deleted their account.

    Assignments are ordered by section_order, then by creation_date, old posts go first.

    The format of creation time is TIME_FORMAT.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    assignment_service = AssignmentService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if not user.isadmin:
            CoursePolicy.assert_course_access(user, course, db)
        assignments = assignment_service.get_course_assignments(course)
        return [Assignment.model_validate(ass) for ass in assignments]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# @router.post("/{assignment_id}/attachment")
# async def create_assignment_attachment(
#     course_id: str,
#     assignment_id: str,
#     file: UploadFile = File(...),
#     user_email: str = Depends(get_current_user),
# ) -> AssignmentAttachmentMetadata:
#     """
#     Attach the provided file to provided course assignment.

#     Filename should contain no more than 80 symbols.

#     Teacher OR Primary Instructor role required.

#     Returns the (course_id, assignment_id, file_id, filename, upload_time) for the new attachment in case of success.

#     The format of upload_time is TIME_FORMAT.
#     """
#     with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
#         return await logic.assignments.create_assignment_attachment(db_conn, db_cursor, storage_db_conn, storage_db_cursor, course_id, assignment_id, file, user_email)


# @router.get("/{assignment_id}/attachment")
# async def get_assignment_attachments(
#     course_id: str,
#     assignment_id: str,
#     user_email: str = Depends(get_current_user)
# ) -> list[AssignmentAttachmentMetadata]:
#     """
#     Get the list of course assignment attachments by provided course_id, assignment_id.

#     Returns list of attachments metadata (course_id, assignment_id, file_id, filename, upload_time).

#     The format of upload_time is TIME_FORMAT.

#     Course role (Primary Instructor, Teacher, Student, Parent) required.
#     """
#     with get_db() as (db_conn, db_cursor):
#         return logic.assignments.get_assignment_attachments(db_cursor, course_id, assignment_id, user_email)


# @router.get("/{assignment_id}/attachment/{file_id}")
# async def download_assignment_attachment(
#     course_id: str,
#     assignment_id: str,
#     file_id: str,
#     user_email: str = Depends(get_current_user)
# ):
#     """
#     Download the course assignment attachment by provided course_id, assignment_id, file_id.

#     Course role (Primary Instructor, Teacher, Student, Parent) required.
#     """
#     with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
#         return logic.assignments.download_assignment_attachment(db_cursor, storage_db_cursor, course_id, assignment_id, file_id, user_email)
