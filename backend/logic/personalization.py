from typing import List
from fastapi import HTTPException
import repo.courses
import repo.personalization
import logic.logging as logger
import constraints

def change_courses_order(db_conn, db_cursor, new_order: List[str], user_email: str):
    if not isinstance(new_order, list):
        raise HTTPException(status_code=400, detail="Provided parameter new_order is not a list")

    if not all(isinstance(i, str) for i in new_order):
        raise HTTPException(status_code=400, detail="Provided parameter new_order is not a list of strings")

    course_ids = [str(crs[0]) for crs in repo.courses.sql_select_available_courses(db_cursor, user_email)]
    if len(new_order) != len(course_ids) or set(new_order) != set(course_ids):
        raise HTTPException(status_code=400, detail="Provided parameter new_order does not match with the list of available courses")

    repo.personalization.sql_update_courses_order(db_cursor, new_order, user_email)

    logger.log(db_conn, logger._TAG_PERSONALIZATION, f"User {user_email} changed an order of available courses")
    return {"success": True}

def set_course_emoji(db_conn, db_cursor, course_id: str, emoji_id: int, user_email: str):
    # checking contraints
    constraints.assert_course_access(db_cursor, user_email, course_id)

    repo.personalization.sql_set_course_emoji(db_cursor, course_id, emoji_id, user_email)

    logger.log(db_conn, logger._TAG_PERSONALIZATION, f"User {user_email} set an emoji {emoji_id} for course {course_id}")
    return {"success": True}
