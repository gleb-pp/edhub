from typing import List
from fastapi import HTTPException
from constants import TIME_FORMAT
import constraints
import repo.sections
import logic.logging as logger


def get_course_feed(db_cursor, course_id: str, user_email: str):
    constraints.assert_course_access(db_cursor, user_email, course_id)
    course_feed = repo.sections.sql_select_course_feed(db_cursor, course_id)
    res = [
        {
            "course_id": str(mat[0]),
            "post_id": mat[1],
            "section_id": mat[2],
            "section_name": mat[3],
            "section_order": mat[4],
            "type": mat[5],
            "creation_time": mat[6].strftime(TIME_FORMAT) if mat[6] is not None else None,
            "author": mat[7]
        }
        for mat in course_feed
    ]
    return res


def create_section(db_conn, db_cursor, course_id: str, title: str, user_email: str):
    # checking constraints
    constraints.assert_teacher_access(db_cursor, user_email, course_id)

    section_id = repo.sections.sql_insert_section(db_cursor, course_id, title)

    logger.log(db_conn, logger.TAG_SECTION_ADD, f"User {user_email} created a section {section_id} within the course {course_id}")
    return {"section_id": section_id}


def change_section_order(db_conn, db_cursor, course_id: str, new_order: List[int], user_email: str):
    # checking constraints
    constraints.assert_teacher_access(db_cursor, user_email, course_id)

    if not isinstance(new_order, list):
        raise HTTPException(status_code=400, detail="Provided parameter new_order is not a list")

    if not all(isinstance(i, int) for i in new_order):
        raise HTTPException(status_code=400, detail="Provided parameter new_order is not a list of integers")

    sections = repo.sections.sql_select_sections(db_cursor, course_id)
    if len(new_order) != len(sections) or set(new_order) != set(sections):
        raise HTTPException(status_code=400, detail="Provided parameter new_order does not match with the list of sections at this course")

    repo.sections.sql_update_section_order(db_cursor, course_id, new_order)

    logger.log(db_conn, logger.TAG_SECTION_EDIT, f"User {user_email} changed a section order within the course {course_id}")
    return {"success": True}


def remove_section(db_conn, db_cursor, course_id: str, section_id: int, user_email: str):
    # checking constraints
    constraints.assert_teacher_access(db_cursor, user_email, course_id)
    constraints.assert_section_exists(db_cursor, course_id, section_id)

    sections = repo.sections.sql_select_sections(db_cursor, course_id)
    if len(sections) == 1:
        raise HTTPException(status_code=422, detail="Cannot remove the last section from the course")

    # remove section
    repo.sections.sql_remove_section(db_cursor, course_id, section_id)

    logger.log(db_conn, logger.TAG_SECTION_DEL, f"User {user_email} deleted a section {section_id} from the course {course_id}")
    return {"success": True}
