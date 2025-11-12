from typing import List, Tuple, Optional
from uuid import UUID
from datetime import datetime

def sql_insert_material(db_cursor, course_id: str, section_id: int, title: str, description: str, user_email: str) -> int:
    db_cursor.execute(
        "INSERT INTO course_materials (courseid, sectionid, name, description, timeadded, author) VALUES (%s, %s, %s, %s, now(), %s) RETURNING matid",
        (course_id, section_id, title, description, user_email),
    )
    return db_cursor.fetchone()[0]


def sql_delete_material(db_cursor, course_id: str, material_id: str) -> None:
    db_cursor.execute(
        "DELETE FROM course_materials WHERE courseid = %s AND matid = %s",
        (course_id, material_id),
    )


def sql_select_material(db_cursor, course_id: str, material_id: str) -> Optional[Tuple[UUID, int, int, datetime, str, str, Optional[str]]]:
    db_cursor.execute(
        """
        SELECT courseid, matid, sectionid, timeadded, name, description, author
        FROM course_materials
        WHERE courseid = %s AND matid = %s
        """,
        (course_id, material_id),
    )
    return db_cursor.fetchone()


def sql_insert_material_attachment(db_cursor, storage_db_cursor, course_id: str, material_id: str, filename: str, contents: bytes) -> Tuple[UUID, datetime]:
    storage_db_cursor.execute(
        """
        INSERT INTO files
        (id, content)
        VALUES (gen_random_uuid(), %s)
        RETURNING id
        """,
        (contents, )
    )
    fileid = storage_db_cursor.fetchone()[0]

    db_cursor.execute(
        """
        INSERT INTO material_files
        (courseid, matid, fileid, filename, uploadtime)
        VALUES (%s, %s, %s, %s, now())
        RETURNING fileid, uploadtime
        """,
        (course_id, material_id, fileid, filename),
    )
    return db_cursor.fetchone()


def sql_select_material_attachments(db_cursor, course_id: str, material_id: str) -> List[Tuple[UUID, str, datetime]]:
    db_cursor.execute(
        """
        SELECT fileid, filename, uploadtime
        FROM material_files
        WHERE courseid = %s AND matid = %s
        """,
        (course_id, material_id),
    )
    return db_cursor.fetchall()
