from typing import List
from fastapi import APIRouter, Query, Depends, HTTPException
from auth import get_current_user
from models.common import Success
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
from models.personalization import EmojiID
import logic.users as user_logic
import exceptions.users as user_errors
import logic.courses as course_logic
import exceptions.courses as course_errors
import logic.personalization as personalization_logic
import exceptions.personalization as personalization_errors
from settings.course import course_settings


router = APIRouter(
    tags=["Personalization"]
)


@router.get("/courses/{course_id}/emoji")
async def get_course_emoji(
    db: Annotated[Session, Depends(get_db)],
    course_id: str,
    user_email: str = Depends(get_current_user),
) -> EmojiID:
    """
    Get the personal course emoji id.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        course_logic.assert_course_access(user, course, db)
        return EmojiID(emoji_id=personalization_logic.get_course_emoji(course, user, db))
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.ParticipantRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.put("/courses/order")
async def change_courses_order(
    db: Annotated[Session, Depends(get_db)],
    new_order: List[str] = Query(...),
    user_email: str = Depends(get_current_user),
) -> Success:
    """
    Change the order of courses.

    The list of course_ids should be passed as a new_order parameter.
    """
    try:
        user = user_logic.get_user(user_email, db)
        personalization_logic.change_courses_order(user, new_order, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except personalization_errors.IncorrectCoursesOrderError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/courses/{course_id}/emoji")
async def set_course_emoji(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    emoji_id: int | None = Query(None, ge=0, le=(course_settings.emoji_count - 1)),
    user_email: str = Depends(get_current_user)
) -> Success:
    """
    Set a personal emoji for a course by provided emoji_id.

    emoji_id can be None (if user wants to delete the course emoji).

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        course_logic.assert_course_access(user, course, db)
        personalization_logic.set_course_emoji(course, user, emoji_id, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.ParticipantRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
