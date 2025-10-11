from typing import List
from fastapi import APIRouter, Depends
from auth import get_current_user, get_db
import json_classes
import logic.users


router = APIRouter()


@router.get("/get_user_info", response_model=json_classes.User, tags=["Users"])
async def get_user_info(user_email: str = Depends(get_current_user)):
    """
    Get the info about the user.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_user_info(db_cursor, user_email)


@router.get("/get_user_role", response_model=json_classes.CourseRole, tags=["Users"])
async def get_user_role(course_id: str, user_email: str = Depends(get_current_user)):
    """
    Get the user's role in the provided course.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_user_role(db_cursor, course_id, user_email)


@router.post("/create_user", response_model=json_classes.Account, tags=["Users"])
async def create_user(user: json_classes.UserCreate):
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


@router.post("/login", response_model=json_classes.Account, tags=["Users"])
async def login(user: json_classes.UserLogin):
    """
    Log into user account with provided email and password.

    Returns email and JWT access token for 30 minutes.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.login(db_cursor, user)


@router.patch("/change_password", response_model=json_classes.Success, tags=["Users"])
async def change_password(user: json_classes.UserNewPassword):
    """
    Change the user password to a new one.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.change_password(db_conn, db_cursor, user)


@router.get("/get_instructor_courses", response_model=List[json_classes.CourseID], tags=["Users"])
async def get_instructor_courses(user_email: str = Depends(get_current_user)):
    """
    Get the list of IDs of courses where the provided user is a Primary Instructor.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_instructor_courses(db_cursor, user_email)


@router.delete("/remove_user", response_model=json_classes.Success, tags=["Users"])
async def remove_user(deleted_user_email: str, user_email: str = Depends(get_current_user)):
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


@router.patch("/give_admin_permissions", response_model=json_classes.Success, tags=["Users"])
async def give_admin_permissions(object_email: str, subject_email: str = Depends(get_current_user)):
    """
    Give admin rights to some existing user by their email.

    Admin role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.give_admin_permissions(db_conn, db_cursor, object_email, subject_email)


@router.get("/get_all_users", response_model=List[json_classes.User], tags=["Users"])
async def get_all_users(user_email: str = Depends(get_current_user)):
    """
    Get the list of all users in the system.

    Return the email and name of each user.

    Admin role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_all_users(db_cursor, user_email)


@router.get("/get_admins", response_model=List[json_classes.User], tags=["Users"])
async def get_admins(user_email: str = Depends(get_current_user)):
    """
    Get the list of platform administrators.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.users.get_admins(db_cursor)
