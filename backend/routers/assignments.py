from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
from fastapi import APIRouter, Depends, Query, UploadFile, File
from auth import get_current_user, get_storage_db
from models.common import Success
from models.assignments import (
    AssignmentID,
    Assignment,
    AssignmentAttachmentMetadata
)
import logic.assignments


router = APIRouter(
    prefix="/{course_id}/assignments",
    tags=["Assignments"],
)


@router.post("/{section_id}")
async def create_assignment(
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
    db: Annotated[Session, Depends(get_db)],
) -> AssignmentID:
    """
    Create the assignment with provided title and description within the section by provided section_id within the course with provided course_id.

    Title can contain only letters, digits, spaces, and underscores.

    Title must contain from 3 to 80 symbols.

    Description must contain from 3 to 10000 symbols.

    Teacher OR Primary Instructor role required.

    Returns the (course_id, assignment_id, section_id) for the new assignment in case of success.
    """

    # connection to database
    with get_db() as (db_conn, db_cursor):
        return logic.assignments.create_assignment(db_conn, db_cursor, course_id, section_id, title, description, user_email)


@router.delete("/{assignment_id}")
async def remove_assignment(
    course_id: str,
    assignment_id: str,
    user_email: str = Depends(get_current_user)
) -> Success:
    """
    Remove the assignment by the provided course_id and assignment_id.

    Teacher OR Primary Instructor role required.
    """

    # connection to database
    with get_db() as (db_conn, db_cursor):
        return logic.assignments.remove_assignment(db_conn, db_cursor, course_id, assignment_id, user_email)


@router.get("/{assignment_id}")
async def get_assignment(
    course_id: str,
    assignment_id: str,
    user_email: str = Depends(get_current_user)
) -> Assignment:
    """
    Get the assignment details by the provided (course_id, assignment_id).

    Returns course_id, assignment_id, section_id, creation_time, title, description, and email of the author.

    Author can be NULL if the author deleted their account.

    The format of creation time is TIME_FORMAT.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """

    # connection to database
    with get_db() as (db_conn, db_cursor):
        return logic.assignments.get_assignment(db_cursor, course_id, assignment_id, user_email)


@router.get("/")
async def get_course_assignments(
    course_id: str,
    user_email: str = Depends(get_current_user)
) -> list[Assignment]:
    """
    Get the list of course assignments by the provided course_id.

    For each assignment, it returns course_id, assignment_id, section_id, creation_time, title, description, and email of the author.

    Author can be NULL if the author deleted their account.

    Assignments are ordered by section_order, then by creation_date, old posts go first.

    The format of creation time is TIME_FORMAT.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """

    # connection to database
    with get_db() as (db_conn, db_cursor):
        return logic.assignments.get_course_assignments(db_cursor, course_id, user_email)


@router.post("/{assignment_id}/attachment")
async def create_assignment_attachment(
    course_id: str,
    assignment_id: str,
    file: UploadFile = File(...),
    user_email: str = Depends(get_current_user),
) -> AssignmentAttachmentMetadata:
    """
    Attach the provided file to provided course assignment.

    Filename should contain no more than 80 symbols.

    Teacher OR Primary Instructor role required.

    Returns the (course_id, assignment_id, file_id, filename, upload_time) for the new attachment in case of success.

    The format of upload_time is TIME_FORMAT.
    """
    with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
        return await logic.assignments.create_assignment_attachment(db_conn, db_cursor, storage_db_conn, storage_db_cursor, course_id, assignment_id, file, user_email)


@router.get("/{assignment_id}/attachment")
async def get_assignment_attachments(
    course_id: str,
    assignment_id: str,
    user_email: str = Depends(get_current_user)
) -> list[AssignmentAttachmentMetadata]:
    """
    Get the list of course assignment attachments by provided course_id, assignment_id.

    Returns list of attachments metadata (course_id, assignment_id, file_id, filename, upload_time).

    The format of upload_time is TIME_FORMAT.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.assignments.get_assignment_attachments(db_cursor, course_id, assignment_id, user_email)


@router.get("/{assignment_id}/attachment/{file_id}")
async def download_assignment_attachment(
    course_id: str,
    assignment_id: str,
    file_id: str,
    user_email: str = Depends(get_current_user)
):
    """
    Download the course assignment attachment by provided course_id, assignment_id, file_id.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
        return logic.assignments.download_assignment_attachment(db_cursor, storage_db_cursor, course_id, assignment_id, file_id, user_email)
