from fastapi import APIRouter, Depends
from auth import get_current_user, get_db
import json_classes
import logic.users


router = APIRouter(
    prefix='/users',
    tags=["Users"],
)


@router.get("{user_email}/info")
async def get_user_info(
    user_email: str = Depends(get_current_user)
) -> json_classes.User:
    """
    Get the info about the user.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_user_info(db_cursor, user_email)


@router.get("/{user_email}/role")
async def get_user_role(
    course_id: str,
    user_email: str = Depends(get_current_user)
) -> json_classes.CourseRole:
    """
    Get the user's role in the provided course.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_user_role(db_cursor, course_id, user_email)


@router.post("/")
async def create_user(user: json_classes.UserCreate) -> json_classes.Account:
    """
    Creates a user account with provided email, name, and password.

    User email should be in the correct format.

    User name can contain only letters, digits, spaces, and underscores; user name can not start with digit.

    User name must contains from 1 to 80 symbols.

    User password should have at least 8 symbols and contain digits, letters, and special symbols.

    Returns email and JWT access token for 30 minutes.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.create_user(db_conn, db_cursor, user)


@router.post("/login")
async def login(user: json_classes.UserLogin) -> json_classes.Account:
    """
    Log into user account with provided email and password.

    Returns email and JWT access token for 30 minutes.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.login(db_cursor, user)


@router.patch("/change_password")
async def change_password(user: json_classes.UserNewPassword) -> json_classes.Success:
    """
    Change the user password to a new one.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.change_password(db_conn, db_cursor, user)


@router.get("/instructor_courses")
async def get_instructor_courses(
    user_email: str = Depends(get_current_user)
) -> list[json_classes.CourseID]:
    """
    Get the list of IDs of courses where the provided user is a Primary Instructor.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_instructor_courses(db_cursor, user_email)


@router.delete("/{deleted_user_email}")
async def remove_user(
    deleted_user_email: str,
    user_email: str = Depends(get_current_user)
) -> json_classes.Success:
    """
    Delete user account from the system.

    The user will be removed from courses where they were a Parent, Student, or Teacher.

    Courses where the user is the Primary Instructor will be deleted.

    The user's assignment submissions will be removed.

    The user's materials and assignments will be left but with NULL author.

    User CAN NOT be deleted if they are the only platform administrator.

    Admin can remove other users
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.remove_user(db_conn, db_cursor, deleted_user_email, user_email)


# TODO: to admin.py
@router.patch("/give_admin_permissions")
async def give_admin_permissions(
    object_email: str,
    subject_email: str = Depends(get_current_user)
) -> json_classes.Success:
    """
    Give admin rights to some existing user by their email.

    Admin role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.give_admin_permissions(db_conn, db_cursor, object_email, subject_email)


@router.get("/")
async def get_all_users(
    user_email: str = Depends(get_current_user)
) -> list[json_classes.User]:
    """
    Get the list of all users in the system.

    Return the email and name of each user.

    Admin role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_all_users(db_cursor, user_email)


# TODO: to admin.py
@router.get("/get_admins")
async def get_admins(
    user_email: str = Depends(get_current_user)
) -> list[json_classes.User]:
    """
    Get the list of platform administrators.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_admins(db_cursor)
