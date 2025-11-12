from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from jose import jwt
import constraints
from auth import pwd_hasher, ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY, ALGORITHM
import repo.users as repo_users
from regex import match, search
import logic.logging as logger
from settings.user import user_settings


def get_user_info(db_cursor, user_email: str):
    return {
        "email": user_email,
        "name": repo_users.sql_get_user_name(db_cursor, user_email),
    }


def get_user_role(db_cursor, course_id: str, user_email: str):
    # getting info about the roles
    res = {
        "is_instructor": constraints.check_instructor_access(db_cursor, user_email, course_id),
        "is_teacher": constraints.check_teacher_access(db_cursor, user_email, course_id),
        "is_student": constraints.check_student_access(db_cursor, user_email, course_id),
        "is_parent": constraints.check_parent_access(db_cursor, user_email, course_id),
        "is_admin": constraints.check_admin_access(db_cursor, user_email)
    }

    return res


def create_user(db_conn, db_cursor, user):

    # validation of email format
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not (
        match(pattern, user.email)
        and len(user.email) <= user_settings.max_email_lenght
        and ".." not in user.email
        and len(user.email.split("@")[0]) <= user_settings.max_email_local_part
    ):
        raise HTTPException(status_code=422, detail="Incorrect email format")

    # validation of username format
    pattern=r"^[\p{L}0-9_ ]+$"
    user.name = user.name.strip()
    if not (
        match(pattern, user.name)
        and user_settings.min_user_name_lenght <= len(user.name) <= user_settings.max_user_name_lenght
        and not(user.name[0].isdigit())
    ):
        raise HTTPException(status_code=422, detail="Incorrect name format")

    # validation of password complexity (length, digit(s), letter(s), special symbol(s))
    if not (
        len(user.password) >= user_settings.pwd_min_lenght
        and search(r"\d", user.password)
        and search(r"\p{L}", user.password)
        and search(r"[^\p{L}\p{N}\s]", user.password)
    ):
        raise HTTPException(status_code=422, detail="Password is too weak")

    # checking whether such user exists
    user_exists = repo_users.sql_select_user_exists(db_cursor, user.email)
    if user_exists:
        raise HTTPException(status_code=409, detail="User already exists")

    # hashing password
    hashed_password = pwd_hasher.hash(user.password)
    repo_users.sql_insert_user(db_cursor, user.email, user.name, hashed_password)

    # giving access_token
    data = {
        "email": user.email,
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    access_token = jwt.encode(data, JWT_SECRET_KEY, algorithm=ALGORITHM)

    logger.log(db_conn, logger.TAG_USER_ADD, f"Created new user: {user.email}")

    return {"email": user.email, "access_token": access_token}


def login(db_cursor, user):

    hashed_password = repo_users.sql_select_passwordhash(db_cursor, user.email)

    # checking whether such user exists
    if not hashed_password:
        raise HTTPException(status_code=401, detail="Invalid user email")

    # checking password
    if not pwd_hasher.verify(user.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    # giving access token
    data = {
        "email": user.email,
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    access_token = jwt.encode(data, JWT_SECRET_KEY, algorithm=ALGORITHM)

    return {"email": user.email, "access_token": access_token}


def change_password(db_conn, db_cursor, user):

    hashed_password = repo_users.sql_select_passwordhash(db_cursor, user.email)

    # checking whether such user exists
    if not hashed_password:
        raise HTTPException(status_code=401, detail="Invalid user email")

    # checking password
    if not pwd_hasher.verify(user.password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    # changing the password to a new one
    hashed_new_password = pwd_hasher.hash(user.new_password)
    repo_users.sql_update_password(db_cursor, user.email, hashed_new_password)

    logger.log(db_conn, logger.TAG_USER_CHPW, f"User {user.email} changed their password")

    return {"success": True}


def get_instructor_courses(db_cursor, user_email: str):
    courses = repo_users.sql_select_instructor_courses(db_cursor, user_email)
    result = [{"course_id": crs} for crs in courses]
    return result


def remove_user(db_conn, db_cursor, deleted_user_email: str, user_email: str):

    # checking constraints
    if not (constraints.check_admin_access(db_cursor, user_email) or
            user_email == deleted_user_email):
        raise HTTPException(status_code=403, detail="User has no right to remove this user")

    constraints.assert_user_exists(db_cursor, deleted_user_email)
    if constraints.check_admin_access(db_cursor, deleted_user_email) and repo_users.sql_count_admins(db_cursor) == 1:
        raise HTTPException(status_code=422, detail="Cannot remove the last administrator")

    # remove user
    repo_users.sql_delete_user(db_cursor, deleted_user_email)


    logger.log(db_conn, logger.TAG_USER_DEL, f"Removed user {deleted_user_email} from the system")

    return {"success": True}


def create_admin_account(db_conn, db_cursor):
    repo_users.sql_insert_user(db_cursor, "admin", "admin", pwd_hasher.hash("admin"))
    repo_users.sql_give_admin_permissions(db_cursor, "admin")

    logger.log(db_conn, logger.TAG_USER_ADD, "Created new user: admin")
    logger.log(db_conn, logger.TAG_ADMIN_ADD, "Added admin privileges to user: admin")


def give_admin_permissions(db_conn, db_cursor, object_email: str, subject_email: str):

    # checking constraints
    constraints.assert_admin_access(db_cursor, subject_email)
    constraints.assert_user_exists(db_cursor, object_email)

    repo_users.sql_give_admin_permissions(db_cursor, object_email)

    logger.log(db_conn, logger.TAG_ADMIN_ADD, f"Added admin privileges to user: {object_email}")

    return {"success": True}


def get_all_users(db_cursor, user_email: str):
    # checking constraints
    constraints.assert_admin_access(db_cursor, user_email)

    # finding all users
    users = repo_users.sql_select_all_users(db_cursor)

    res = [{"email": u[0], "name": u[1]} for u in users]
    return res


def get_admins(db_cursor):
    users = repo_users.sql_select_admins(db_cursor)
    res = [{"email": u[0], "name": u[1]} for u in users]
    return res


# create an initial admin account
async def create_admin_account_if_not_exists(db_conn, db_cursor):
    if repo_users.sql_admins_exist(db_cursor):
        return
    create_admin_account(db_conn, db_cursor)
    print("\nAdmin account created\nlogin: admin\npassword: admin\n")
