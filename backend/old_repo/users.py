from typing import Optional, List, Tuple
from uuid import UUID

def sql_get_user_name(db_cursor, email: str) -> Optional[str]:
    db_cursor.execute("SELECT publicname FROM users WHERE email = %s", (email,))
    row = db_cursor.fetchone()
    return row[0] if row else None


def sql_select_user_exists(db_cursor, email: str) -> bool:
    db_cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE email = %s)", (email,))
    return db_cursor.fetchone()[0]


def sql_insert_user(db_cursor, email: str, name: str, hashed_password: str) -> None:
    db_cursor.execute(
        "INSERT INTO users (email, publicname, isadmin, timeregistered, passwordhash) VALUES (%s, %s, 'f', now(), %s)",
        (email, name, hashed_password),
    )


def sql_select_passwordhash(db_cursor, email: str) -> Optional[str]:
    db_cursor.execute("SELECT passwordhash FROM users WHERE email = %s", (email,))
    row = db_cursor.fetchone()
    return row[0] if row else None


def sql_update_password(db_cursor, email: str, hashed_new_password: str) -> None:
    db_cursor.execute("UPDATE users SET passwordhash = %s WHERE email = %s", (hashed_new_password, email))


def sql_select_instructor_courses(db_cursor, user_email: str) -> List[UUID]:
    db_cursor.execute(
        "SELECT courseid FROM courses WHERE instructor = %s",
        (user_email,),
    )
    return [row[0] for row in db_cursor.fetchall()]


def sql_delete_user(db_cursor, user_email: str) -> None:
    db_cursor.execute("DELETE FROM users WHERE email = %s", (user_email,))


def sql_give_admin_permissions(db_cursor, user_email: str) -> None:
    db_cursor.execute("UPDATE users SET isadmin = 't' WHERE email = %s", (user_email,))


def sql_select_admins(db_cursor) -> List[Tuple[str, str]]:
    db_cursor.execute("SELECT email, publicname FROM users WHERE isadmin")
    return db_cursor.fetchall()


def sql_count_admins(db_cursor) -> int:
    db_cursor.execute("SELECT COUNT(*) FROM users WHERE isadmin")
    return db_cursor.fetchone()[0]


def sql_admins_exist(db_cursor) -> bool:
    db_cursor.execute("SELECT EXISTS (SELECT 1 FROM users WHERE isadmin)")
    return db_cursor.fetchone()[0]


def sql_select_all_users(db_cursor) -> List[Tuple[str, str]]:
    db_cursor.execute("SELECT email, publicname FROM users")
    return db_cursor.fetchall()
