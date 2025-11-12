from fastapi import HTTPException, UploadFile, Response
from constants import TIME_FORMAT
import constraints
import repo.assignments as repo_ass
import repo.files as repo_files
import logic.logging as logger
from logic.uploading import careful_upload


def create_assignment(
    db_conn,
    db_cursor,
    course_id: str,
    section_id: int,
    title: str,
    description: str,
    user_email: str,
):
    # checking constraints
    constraints.assert_teacher_access(db_cursor, user_email, course_id)
    constraints.assert_section_exists(db_cursor, course_id, section_id)

    # create assignment
    assignment_id = repo_ass.sql_insert_assignment(db_cursor, course_id, section_id, title, description, user_email)

    logger.log(db_conn, logger.TAG_ASSIGNMENT_ADD, f"User {user_email} created an assignment {assignment_id} within the section {section_id} in the course {course_id}")

    return {"course_id": course_id, "assignment_id": assignment_id, "section_id": section_id}


def remove_assignment(db_conn, db_cursor, course_id: str, assignment_id: str, user_email: str):
    # checking constraints
    constraints.assert_teacher_access(db_cursor, user_email, course_id)
    constraints.assert_assignment_exists(db_cursor, course_id, assignment_id)

    # remove assignment
    repo_ass.sql_delete_assignment(db_cursor, course_id, assignment_id)

    logger.log(db_conn, logger.TAG_ASSIGNMENT_DEL, f"User {user_email} removed an assignment {assignment_id} from the course {course_id}")

    return {"success": True}


def get_assignment(db_cursor, course_id: str, assignment_id: str, user_email: str):

    # checking constraints
    constraints.assert_course_access(db_cursor, user_email, course_id)

    # searching for the assignment
    assignment = repo_ass.sql_select_assignment(db_cursor, course_id, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    res = {
        "course_id": str(assignment[0]),
        "assignment_id": assignment[1],
        "section_id": assignment[2],
        "creation_time": assignment[3].strftime(TIME_FORMAT),
        "title": assignment[4],
        "description": assignment[5],
        "author": assignment[6],
    }
    return res


def get_course_assignments(db_cursor, course_id: str, user_email: str):

    # checking constraints
    constraints.assert_course_access(db_cursor, user_email, course_id)

    # searching for assignments
    assignments = repo_ass.sql_select_course_assignments(db_cursor, course_id)

    res = [
        {
            "course_id": str(ass[0]),
            "assignment_id": ass[1],
            "section_id": ass[2],
            "creation_time": ass[3].strftime(TIME_FORMAT),
            "title": ass[4],
            "description": ass[5],
            "author": ass[6],
        }
        for ass in assignments
    ]
    return res


async def create_assignment_attachment(db_conn, db_cursor, storage_db_conn, storage_db_cursor, course_id: str, assignment_id: str, file: UploadFile, user_email: str):
    # checking constraints
    constraints.assert_teacher_access(db_cursor, user_email, course_id)
    constraints.assert_assignment_exists(db_cursor, course_id, assignment_id)
    if len(file.filename) > 80:
        raise HTTPException(status_code=422, detail="File name too long")

    # read the file
    contents = await careful_upload(file)

    # save the file into database
    attachment_metadata = repo_ass.sql_insert_assignment_attachment(db_cursor, storage_db_cursor, course_id, assignment_id, file.filename, contents)

    logger.log(db_conn, logger.TAG_ATTACHMENT_ADD_ASS, f"User {user_email} created an attachment {file.filename} for the assignment {assignment_id} in course {course_id}")
    return {
        "course_id": course_id,
        "assignment_id": assignment_id,
        "file_id": attachment_metadata[0],
        "filename" : file.filename,
        "upload_time" : attachment_metadata[1].strftime(TIME_FORMAT)
    }


def get_assignment_attachments(db_cursor, course_id: str, assignment_id: str, user_email: str):
    # checking constraints
    constraints.assert_course_access(db_cursor, user_email, course_id)
    constraints.assert_assignment_exists(db_cursor, course_id, assignment_id)

    # searching for assignment attachments
    files = repo_ass.sql_select_assignment_attachments(db_cursor, course_id, assignment_id)

    res = [{
        "course_id": course_id,
        "assignment_id": assignment_id,
        "file_id": file[0],
        "filename": file[1],
        "upload_time": file[2].strftime(TIME_FORMAT)
    } for file in files]

    return res


def download_assignment_attachment(db_cursor, storage_db_cursor, course_id: str, assignment_id: str, file_id: str, user_email: str):
    # checking constraints
    constraints.assert_course_access(db_cursor, user_email, course_id)
    constraints.assert_assignment_exists(db_cursor, course_id, assignment_id)

    # searching for assignment attachment
    file = repo_files.sql_download_attachment(storage_db_cursor, file_id)
    file_metadata = repo_files.sql_select_attachment_metadata(db_cursor, file_id)
    if (not file or not file_metadata):
        raise HTTPException(status_code=404, detail="Attachment not found")

    return Response(
        content=file,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_metadata[1]}"'}
    )
