from fastapi import APIRouter, Query, Depends
from auth import get_current_user
import logic.sections
from models.common import Success
from models.sections import CoursePost, SectionID
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db


router = APIRouter(
    tags=["Course Sections"],
)


@router.get("/get_course_feed")
async def get_course_feed(
    course_id: str,
    user_email: str = Depends(get_current_user)
) -> list[CoursePost]:
    """
    Get the course feed with all its materials and assignments.

    Returns the list of (course_id, post_id, section_id, section_name, section_order, type, creation_time, author) for each material.

    Rows are ordered by section_order, then by creation_date, old posts go first.

    For sections with no feed in it, there is a string with (post_id, type, creation_time, author) equal to None.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.sections.get_course_feed(db_cursor, course_id, user_email)


@router.post("/create_section")
async def create_section(
    course_id: str,
    title: str = Query(
        ...,
        min_length=3,
        max_length=80,
        pattern=r"^[\p{L}0-9_ ]+$",
        description="Section title can contain only letters, digits, spaces, and underscores, 3-80 symbols"
    ),
    user_email: str = Depends(get_current_user),
) -> SectionID:
    """
    Create the course section with provided title within the course with provided course_id.

    Title contain only letters, digits, spaces, and underscores.

    Title must contains from 3 to 80 symbols.

    Teacher OR Primary Instructor role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.sections.create_section(db_conn, db_cursor, course_id, title, user_email)


@router.put("/change_section_order")
async def change_section_order(
    course_id: str,
    new_order: list[int] = Query(...),
    user_email: str = Depends(get_current_user),
) -> Success:
    """
    Change the order of sections within the course with provided course_id.

    The list of section_ids should be passed as a new_order parameter.

    Teacher OR Primary Instructor role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.sections.change_section_order(db_conn, db_cursor, course_id, new_order, user_email)


@router.delete("/remove_section")
async def remove_section(
    course_id: str,
    section_id: int,
    user_email: str = Depends(get_current_user),
) -> Success:
    """
    Remove the section with provided section_id from the course with provided course_id.

    All the materials and assignments within the removed section will be also removed.

    Impossible to remove the last section from the course.

    Teacher OR Primary Instructor role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.sections.remove_section(db_conn, db_cursor, course_id, section_id, user_email)
