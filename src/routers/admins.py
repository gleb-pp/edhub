from fastapi import APIRouter, Depends, HTTPException
from src.auth import get_current_user
from src.services import UserService, CourseService
from src.policies import AdminPolicy
from src.exceptions import users as user_errors, admins as admin_errors
from src.models.common import Success
from src.models.users import User
from src.models.courses import Course
from typing import Annotated
from sqlalchemy.orm import Session
from src.db import get_db

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.delete("/user")
async def remove_user(
    deleted_user_email: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> Success:
    """
    Delete user account from the system.

    The user will be removed from courses where they were a Parent, Student, or Teacher.

    Courses where the user is the Primary Instructor will be deleted.

    The user's assignment submissions will be removed.

    The user's materials and assignments will be left but with NULL author.

    User CAN NOT be deleted if they are the only platform administrator.

    Admin can remove other users.
    """
    user_service = UserService(db)
    try:
        user = user_service.get_user(user_email)
        AdminPolicy.assert_user_is_admin(user)
        deleted_user = user_service.get_user(deleted_user_email)
        user_service.delete_user(deleted_user)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == user_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        elif e.email == deleted_user_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        admin_errors.AdminRoleRequiredError,
        admin_errors.DeleteLastAdminError,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.patch("/give_admin_permissions")
async def give_admin_permissions(
    new_admin_email: str,
    db: Annotated[Session, Depends(get_db)],
    admin_email: str = Depends(get_current_user),
) -> Success:
    """
    Give admin rights to some existing user by their email.

    Admin role required.
    """
    user_service = UserService(db)
    try:
        admin = user_service.get_user(admin_email)
        AdminPolicy.assert_user_is_admin(admin)
        new_admin = user_service.get_user(new_admin_email)
        user_service.give_admin_permissions(new_admin)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == admin_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        elif e.email == new_admin_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except admin_errors.AdminRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/users")
async def get_all_users(
    db: Annotated[Session, Depends(get_db)],
    admin_email: str = Depends(get_current_user),
) -> list[User]:
    """
    Get the list of all users in the system.

    Return the email and name of each user.

    Admin role required.
    """
    user_service = UserService(db)
    try:
        admin = user_service.get_user(admin_email)
        AdminPolicy.assert_user_is_admin(admin)
        users = user_service.get_all_users()
        return [User.model_validate(u) for u in users]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except admin_errors.AdminRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/get_admins")
async def get_admins(
    db: Annotated[Session, Depends(get_db)],
) -> list[User]:
    """
    Get the list of platform administrators.
    """
    user_service = UserService(db)
    admins = user_service.get_admins()
    return [User.model_validate(a) for a in admins]


@router.get("/get_all_courses")
async def get_all_courses(
    db: Annotated[Session, Depends(get_db)],
    admin_email: str = Depends(get_current_user),
) -> list[Course]:
    """
    Get the list of all courses in the system.

    For each course, returns (course_id, title, organization, instructor_email, and creation_time).

    Admin role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    try:
        admin = user_service.get_user(admin_email)
        AdminPolicy.assert_user_is_admin(admin)
        courses = course_service.get_all_courses()
        return [Course.model_validate(c) for c in courses]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except admin_errors.AdminRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
