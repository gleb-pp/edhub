from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from auth import get_current_user, get_db
import json_classes
import logic.courses


router = APIRouter()


@router.get("/available_courses", response_model=List[json_classes.Course], tags=["Courses"])
async def available_courses(user_email: str = Depends(get_current_user)):
    """
    Get the list of of courses available for user (as a Primary Instructor, Teacher, Student, or Parent).

    For each course, returns (course_id, title, instructor_email, instructor_name, organization, creation_time, personal emoji_id).
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.available_courses(db_cursor, user_email)


@router.get("/get_all_courses", response_model=List[json_classes.Course], tags=["Courses"])
async def get_all_courses(user_email: str = Depends(get_current_user)):
    """
    Get the list of all courses in the system.

    For each course, returns (course_id, title, instructor_email, instructor_name, organization, creation_time, personal emoji_id).

    Admin role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.get_all_courses(db_cursor, user_email)


@router.post("/create_course", response_model=json_classes.CourseID, tags=["Courses"])
async def create_course(
    title: str = Query(
        ...,
        min_length=3,
        max_length=80,
        pattern=r"^[\p{L}0-9_ ]+$",
        description="Title can contain only letters, digits, spaces, and underscores, 3-80 symbols"
    ),
    organization: Optional[str] = Query(
        None,
        min_length=3,
        max_length=80,
        pattern=r"^[\p{L}0-9_ ]+$",
        description="Organization can contain only letters, digits, spaces, and underscores, 3-80 symbols"
    ),
    user_email: str = Depends(get_current_user),
):
    """
    Create the course with provided title and become a Primary Instructor in it.

    Title and Organization can contain only letters, digits, spaces, and underscores.

    Title and Organization must contains from 3 to 80 symbols.

    Organization parameter is optional / can be None.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.create_course(db_conn, db_cursor, title, user_email, organization)


@router.delete("/remove_course", response_model=json_classes.Success, tags=["Courses"])
async def remove_course(course_id: str, user_email: str = Depends(get_current_user)):
    """
    Remove the course with provided course_id.

    All the course materials, teachers, students, and parents will be also removed.

    Primary Instructor role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.remove_course(db_conn, db_cursor, course_id, user_email)


@router.get("/get_course_info", response_model=json_classes.Course, tags=["Courses"])
async def get_course_info(course_id: str, user_email: str = Depends(get_current_user)):
    """
    Get information about the course: course_id, title, instructor_email, instructor_name, organization, creation_time, and personal emoji_id.

    emoji_id is optional (can be None).

    Organization can be None.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.courses.get_course_info(db_cursor, course_id, user_email)
