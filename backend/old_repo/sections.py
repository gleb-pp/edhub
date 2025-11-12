from typing import List, Tuple, Optional
from uuid import UUID
from datetime import datetime


def sql_select_course_feed(db_cursor, course_id: str) -> List[Tuple[UUID, Optional[int], int, str, int, Optional[str], Optional[datetime], Optional[str]]]:
    db_cursor.execute(
        """
        SELECT cs.courseid, feed.postid, cs.sectionid, cs.name, cs.sectionorder, feed.type, feed.timeadded, feed.author
        FROM
            (SELECT courseid AS cid, matid as postid, sectionid, 'mat' as type, timeadded, author
            FROM course_materials
            WHERE courseid = %s
            UNION
            SELECT courseid AS cid, assid as postid, sectionid, 'ass' as type, timeadded, author
            FROM course_assignments
            WHERE courseid = %s) feed
            RIGHT JOIN
                (SELECT courseid, sectionid, name, sectionorder
                FROM course_sections
                WHERE courseid = %s) cs ON feed.sectionid = cs.sectionid
        ORDER BY cs.sectionorder ASC, feed.timeadded ASC
        """,
        (course_id, course_id, course_id),
    )
    return db_cursor.fetchall()


def sql_insert_section(db_cursor, course_id: str, title: str) -> int:
    db_cursor.execute(
        """
        INSERT INTO course_sections (courseid, name, sectionorder)
        VALUES (%s, %s,
            (SELECT COALESCE(MAX(sectionorder), -1) + 1 FROM course_sections WHERE courseid = %s)
        )
        RETURNING sectionid
        """,
        (course_id, title, course_id),
    )
    return db_cursor.fetchone()[0]


def sql_select_sections(db_cursor, course_id: str) -> List[int]:
    db_cursor.execute(
        """
        SELECT sectionid FROM course_sections WHERE courseid = %s
        """,
        (course_id, ),
    )
    return [i[0] for i in db_cursor.fetchall()]


def sql_update_section_order(db_cursor, course_id: str, new_order: List[int]) -> None:

    # postpone the checking of uniqueness constraints
    db_cursor.execute("SET CONSTRAINTS course_sections_courseid_sectionorder_key DEFERRED")

    # set correct values
    values_to_update = [(section_id, index) for index, section_id in enumerate(new_order)]
    values_str = ", ".join("(%s, %s)" for _ in values_to_update)
    flat_values = [val for pair in values_to_update for val in pair]
    db_cursor.execute(f"""
        UPDATE course_sections cs
        SET sectionorder = new.sectionorder
        FROM (VALUES {values_str}) AS new(sectionid, sectionorder)
        WHERE cs.courseid = %s AND cs.sectionid = new.sectionid
        """,
        [*flat_values, course_id]
    )

def sql_remove_section(db_cursor, course_id: str, section_id: int) -> None:
    db_cursor.execute(
        """
        DELETE FROM course_sections
        WHERE courseid = %s AND sectionid = %s
        """
        , (course_id, section_id)
    )
