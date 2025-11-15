from typing import List
from fastapi import APIRouter, Query, Depends
from auth import get_current_user
from constants import EMOJI_COUNT
from models.common import Success
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db


router = APIRouter(
    tags=["Personalization"]
)

# TODO: get_course_emoji


@router.put("/courses/order")
async def change_courses_order(
    new_order: List[str] = Query(...),
    user_email: str = Depends(get_current_user),
) -> Success:
    """
    Change the order of courses.

    The list of course_ids should be passed as a new_order parameter.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.personalization.change_courses_order(db_conn, db_cursor, new_order, user_email)


@router.patch("/courses/{course_id}/emoji")
async def set_course_emoji(
    course_id: str,
    emoji_id: int = Query(..., ge=0, le=EMOJI_COUNT),
    user_email: str = Depends(get_current_user)
) -> Success:
    """
    Set a personal emoji for a course.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.personalization.set_course_emoji(db_conn, db_cursor, course_id, emoji_id, user_email)
