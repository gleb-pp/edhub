from typing import List

def sql_update_courses_order(db_cursor, new_order: List[str], user_email: str) -> None:

    # postpone the checking of uniqueness constraints
    db_cursor.execute("SET CONSTRAINTS personal_course_info_email_courseorder_key DEFERRED")

    # set correct values
    values_to_update = [(course_id, index) for index, course_id in enumerate(new_order)]
    values_str = ", ".join("(%s, %s)" for _ in values_to_update)
    flat_values = [val for pair in values_to_update for val in pair]
    db_cursor.execute(f"""
        UPDATE personal_course_info pci
        SET courseorder = new.courseorder
        FROM (VALUES {values_str}) AS new(courseid, courseorder)
        WHERE pci.email = %s AND pci.courseid = new.courseid::uuid
        """,
        [*flat_values, user_email]
    )


def sql_set_course_emoji(db_cursor, course_id: str, emoji_id: int, user_email: str) -> None:
    db_cursor.execute(
        """
        UPDATE personal_course_info
        SET emojiid = %s
        WHERE email = %s AND courseid = %s::uuid
        """,
        (emoji_id, user_email, course_id)
    )
