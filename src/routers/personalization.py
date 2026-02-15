from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.auth import get_current_user
from src.db import get_db
from src.exceptions import courses as course_errors
from src.exceptions import personalization as personalization_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.models.personalization import EmojiID
from src.policies import CoursePolicy
from src.services import CourseService, PersonalizationService, UserService
from src.settings.course import course_settings

router = APIRouter(tags=["Personalization"])


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
    user_service = UserService(db)
    course_service = CourseService(db)
    personalization_service = PersonalizationService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        CoursePolicy.assert_course_access(user, course, db)
        return EmojiID(emoji_id=personalization_service.get_course_emoji(course, user))
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.ParticipantRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.put("/courses/order")
async def change_courses_order(
    db: Annotated[Session, Depends(get_db)],
    new_order: list[str] = Query(...),
    user_email: str = Depends(get_current_user),
) -> Success:
    """
    Change the order of courses.

    The list of course_ids should be passed as a new_order parameter.
    """
    user_service = UserService(db)
    personalization_service = PersonalizationService(db)
    try:
        user = user_service.get_user(user_email)
        personalization_service.change_courses_order(user, new_order)
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
    user_email: str = Depends(get_current_user),
) -> Success:
    """
    Set a personal emoji for a course by provided emoji_id.

    emoji_id can be None (if user wants to delete the course emoji).

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    personalization_service = PersonalizationService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        CoursePolicy.assert_course_access(user, course, db)
        personalization_service.set_course_emoji(course, user, emoji_id)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.ParticipantRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
