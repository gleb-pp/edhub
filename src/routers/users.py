from fastapi import APIRouter, Depends, HTTPException
from src.auth import get_current_user
from src.services import UserService, CourseService
from src.policies import TeacherPolicy, StudentPolicy, ParentPolicy
from src.exceptions import (
    users as user_errors,
    courses as course_errors,
    admins as admin_errors,
)
from src.models.common import Success
from src.models.courses import CourseID
from src.models.users import User, CourseRole, AccessToken
from typing import Annotated
from sqlalchemy.orm import Session
from src.db import get_db

router = APIRouter(
    tags=["Users"],
)


@router.get("/users/{user_email}")
async def get_user_info(
    user_email: str,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get the info about the user.
    """
    try:
        user_service = UserService(db)
        user = user_service.get_user(user_email)
        return User.model_validate(user)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/course/{course_id}/me/role")
async def get_my_role(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> CourseRole:
    """
    Get the user's role in the provided course.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        return CourseRole(
            is_instructor=TeacherPolicy.check_instructor_access(user, course, db),
            is_teacher=TeacherPolicy.check_teacher_access(user, course, db),
            is_student=StudentPolicy.check_student_access(user, course, db),
            is_parent=ParentPolicy.check_parent_access(user, course, db),
            is_admin=user.isadmin,
        )
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/users")
async def create_user(
    email: str, name: str, password: str, db: Annotated[Session, Depends(get_db)]
) -> AccessToken:
    """
    Creates a user account with provided email, name, and password.

    User email should be in the correct format.

    User name can contain only letters, digits, spaces, and underscores; user name can not start with digit.

    User name must contains from 1 to 80 symbols.

    User password should have at least 8 symbols and contain digits, letters, and special symbols.

    Returns email and JWT access token for 30 minutes.
    """
    user_service = UserService(db)
    try:
        user_service.validate_user_email(email)
        user_service.validate_user_name(name)
        user_service.validate_password_length(password)
        user = user_service.create_user(email, name, password)
        token = user_service.get_access_token(user)
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
    user_service = UserService(db)
    try:
        user = user_service.get_user(email)
        user_service.verify_password(user, password)
        token = user_service.get_access_token(user)
        return AccessToken(access_token=token)
    except user_errors.UserError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.patch("/users/me/password")
async def change_password(
    email: str,
    password: str,
    new_password: str,
    db: Annotated[Session, Depends(get_db)],
) -> Success:
    """
    Change the user password to a new one.
    """
    user_service = UserService(db)
    try:
        user = user_service.get_user(email)
        user_service.verify_password(user, password)
        user_service.validate_password_length(new_password)
        user_service.change_password(user, new_password)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/users/instructor_courses")
async def get_my_instructor_courses(
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> list[CourseID]:
    """
    Get the list of IDs of courses where the provided user is a Primary Instructor.
    """
    user_service = UserService(db)
    try:
        user = user_service.get_user(user_email)
        courses = user_service.get_instructor_courses(user)
        return [CourseID.model_validate(course) for course in courses]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.delete("/users/me")
async def remove_user(
    db: Annotated[Session, Depends(get_db)], user_email: str = Depends(get_current_user)
) -> Success:
    """
    Delete user account from the system.

    The user will be removed from courses where they were a Parent, Student, or Teacher.

    Courses where the user is the Primary Instructor will be deleted.

    The user's assignment submissions will be removed.

    The user's materials and assignments will be left but with NULL author.

    User CAN NOT be deleted if they are the only platform administrator.
    """
    user_service = UserService(db)
    try:
        user = user_service.get_user(user_email)
        user_service.delete_user(user)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except admin_errors.DeleteLastAdminError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
