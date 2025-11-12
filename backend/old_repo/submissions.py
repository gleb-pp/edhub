from typing import List, Tuple, Optional
from uuid import UUID
from datetime import datetime


def sql_insert_submission(db_cursor, course_id: str, assignment_id: str, student_email: str, submission_text: str) -> None:
    db_cursor.execute(
        "INSERT INTO course_assignments_submissions (courseid, assid, email, timeadded, timemodified, submissiontext, grade, comment, gradedby) VALUES (%s, %s, %s, now(), now(), %s, null, null, null)",
        (course_id, assignment_id, student_email, submission_text),
    )


def sql_insert_submission_attachment(db_cursor, storage_db_cursor, course_id: str, assignment_id: str, student_email: str, filename: str, contents: bytes) -> Tuple[UUID, datetime]:
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
        INSERT INTO submissions_files
        (courseid, assid, email, fileid, filename, uploadtime)
        VALUES (%s, %s, %s, %s, %s, now())
        RETURNING fileid, uploadtime
        """,
        (course_id, assignment_id, student_email, fileid, filename),
    )
    return db_cursor.fetchone()


def sql_select_submission_attachments(db_cursor, course_id: str, assignment_id: str, student_email: str) -> List[Tuple[UUID, str, datetime]]:
    db_cursor.execute(
        """
        SELECT fileid, filename, uploadtime
        FROM submissions_files
        WHERE courseid = %s AND assid = %s AND email = %s
        """,
        (course_id, assignment_id, student_email),
    )
    return db_cursor.fetchall()


def sql_update_submission_text(db_cursor, submission_text: str, course_id: str, assignment_id: str, student_email: str) -> None:
    db_cursor.execute(
        """
        UPDATE course_assignments_submissions
        SET submissiontext = %s, timemodified = now()
        WHERE courseid = %s AND assid = %s AND email = %s
        """,
        (submission_text, course_id, assignment_id, student_email),
    )


def sql_select_submissions(db_cursor, course_id: str, assignment_id: str) -> List[Tuple[str, str, datetime, datetime, str, Optional[int], Optional[str], Optional[str], Optional[str]]]:
    db_cursor.execute(
        """
        SELECT
            s.email,
            st.publicname,
            s.timeadded,
            s.timemodified,
            s.submissiontext,
            s.grade,
            s.comment,
            s.gradedby,
            tch.publicname
        FROM course_assignments_submissions s
        JOIN users st ON s.email = st.email
        LEFT JOIN users tch ON s.gradedby = tch.email
        WHERE s.courseid = %s AND s.assid = %s
        ORDER BY s.timeadded DESC
        """,
        (course_id, assignment_id),
    )
    return db_cursor.fetchall()


def sql_select_single_submission(db_cursor, course_id: str, assignment_id: str, student_email: str) -> Optional[Tuple[str, str, datetime, datetime, str, Optional[int], Optional[str], Optional[str], Optional[str]]]:
    db_cursor.execute(
        """
        SELECT
            s.email,
            st.publicname,
            s.timeadded,
            s.timemodified,
            s.submissiontext,
            s.grade,
            s.comment,
            s.gradedby,
            tch.publicname
        FROM course_assignments_submissions s
        JOIN users st ON s.email = st.email
        LEFT JOIN users tch ON s.gradedby = tch.email
        WHERE s.courseid = %s AND s.assid = %s AND s.email = %s
        """,
        (course_id, assignment_id, student_email),
    )
    return db_cursor.fetchone()
