from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from jose import jwt
import constraints
from auth import pwd_hasher, ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY, ALGORITHM
import repo.users as repo_users
from regex import match, search
import logic.logging as logger
from settings.user import user_settings



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
