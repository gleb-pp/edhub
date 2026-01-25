from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from services import (
    users as user_logic,
    courses as course_logic,
    teachers as teacher_logic,
    students as student_logic,
    parents as parent_logic,
)
from exceptions import (
    users as user_errors,
    courses as course_errors,
    admins as admin_errors
)
from models.common import Success
from models.courses import CourseID
from models.users import (
    User,
    CourseRole,
    AccessToken,
)
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db


router = APIRouter(
    prefix='/users',
    tags=["Users"],
)


@router.get("/{user_email}")
async def get_user_info(
    user_email: str,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get the info about the user.
    """
    try:
        user = user_logic.get_user(user_email, db)
        return User.model_validate(user)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{course_id}")
async def get_my_role(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> CourseRole:
    """
    Get the user's role in the provided course.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        return CourseRole(
            is_instructor=teacher_logic.check_instructor_access(user, course, db),
            is_teacher=teacher_logic.check_teacher_access(user, course, db),
            is_student=student_logic.check_student_access(user, course, db),
            is_parent=parent_logic.check_parent_access(user, course, db),
            is_admin=user.isadmin
        )
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/")
async def create_user(
    email: str,
    name: str,
    password: str,
    db: Annotated[Session, Depends(get_db)]
) -> AccessToken:
    """
    Creates a user account with provided email, name, and password.

    User email should be in the correct format.

    User name can contain only letters, digits, spaces, and underscores; user name can not start with digit.

    User name must contains from 1 to 80 symbols.

    User password should have at least 8 symbols and contain digits, letters, and special symbols.

    Returns email and JWT access token for 30 minutes.
    """
    try:
        user_logic.validate_user_email(email)
        user_logic.validate_user_name(name)
        user_logic.validate_password_lenght(password)
        user = user_logic.create_user(email, name, password, db)
        token = user_logic.get_access_token(user)
        db.commit()
        return AccessToken(access_token=token)
    except (
        user_errors.EmailFormatError,
        user_errors.NameFormatError,
        user_errors.WeakPasswordError,
    ) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except user_errors.UserExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/login")
async def login(
    email: str,
    password: str,
    db: Annotated[Session, Depends(get_db)],
) -> AccessToken:
    """
    Log into user account with provided email and password.

    Returns email and JWT access token for 30 minutes.
    """
    try:
        user = user_logic.get_user(email, db)
        user_logic.verify_password(user, password)
        token = user_logic.get_access_token(user)
        return AccessToken(access_token=token)
    except user_errors.UserError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.patch("/change_password")
async def change_password(
    email: str,
    password: str,
    new_password: str,
    db: Annotated[Session, Depends(get_db)],
) -> Success:
    """
    Change the user password to a new one.
    """
    try:
        user = user_logic.get_user(email, db)
        user_logic.verify_password(user, password)
        user_logic.validate_password_lenght(new_password)
        user_logic.change_password(user, new_password)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/instructor_courses")
async def get_my_instructor_courses(
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> list[CourseID]:
    """
    Get the list of IDs of courses where the provided user is a Primary Instructor.
    """
    try:
        user = user_logic.get_user(user_email, db)
        courses = user_logic.get_instructor_courses(user, db)
        return [CourseID.model_validate(course) for course in courses]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.delete("/")
async def remove_user(
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user)
) -> Success:
    """
    Delete user account from the system.

    The user will be removed from courses where they were a Parent, Student, or Teacher.

    Courses where the user is the Primary Instructor will be deleted.

    The user's assignment submissions will be removed.

    The user's materials and assignments will be left but with NULL author.

    User CAN NOT be deleted if they are the only platform administrator.
    """
    try:
        user = user_logic.get_user(user_email, db)
        user_logic.delete_user(user, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except admin_errors.DeleteLastAdminError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
