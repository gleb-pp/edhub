from fastapi import APIRouter, Query, Depends
from auth import get_current_user
from models.courses import CourseID, Course
from models.common import Success
import logic.courses
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


@router.get("/")
async def get_available_courses(
    user_email: str = Depends(get_current_user)
) -> list[Course]:
    """
    Get the list of of courses available for user (as a Primary Instructor, Teacher, Student, or Parent).

    For each course, returns (course_id, title, instructor_email, instructor_name, organization, creation_time, personal emoji_id).
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.available_courses(db_cursor, user_email)


# TODO: to admin.py
@router.get("/get_all_courses")
async def get_all_courses(
    user_email: str = Depends(get_current_user)
) -> list[Course]:
    """
    Get the list of all courses in the system.

    For each course, returns (course_id, title, instructor_email, instructor_name, organization, creation_time, personal emoji_id).

    Admin role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.get_all_courses(db_cursor, user_email)


@router.post("/")
async def create_course(
    title: str = Query(
        ...,
        min_length=3,
        max_length=80,
        pattern=r"^[\p{L}0-9_ ]+$",
        description="Title can contain only letters, digits, spaces, and underscores, 3-80 symbols"
    ),
    organization: str | None = Query(
        None,
        min_length=3,
        max_length=80,
        pattern=r"^[\p{L}0-9_ ]+$",
        description="Organization can contain only letters, digits, spaces, and underscores, 3-80 symbols"
    ),
    user_email: str = Depends(get_current_user),
) -> CourseID:
    """
    Create the course with provided title and become a Primary Instructor in it.

    Title and Organization can contain only letters, digits, spaces, and underscores.

    Title and Organization must contains from 3 to 80 symbols.

    Organization parameter is optional / can be None.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.create_course(db_conn, db_cursor, title, user_email, organization)


@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    user_email: str = Depends(get_current_user)
) -> Success:
    """
    Remove the course with provided course_id.

    All the course materials, teachers, students, and parents will be also removed.

    Primary Instructor role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.remove_course(db_conn, db_cursor, course_id, user_email)


@router.get("/{course_id}")
async def get_course_info(
    course_id: str,
    user_email: str = Depends(get_current_user)
) -> Course:
    """
    Get information about the course: course_id, title, instructor_email, instructor_name, organization, creation_time, and personal emoji_id.

    emoji_id is optional (can be None).

    Organization can be None.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.get_course_info(db_cursor, course_id, user_email)
