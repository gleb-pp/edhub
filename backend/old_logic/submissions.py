from fastapi import HTTPException, UploadFile, Response
from constants import TIME_FORMAT
import constraints
import repo.submissions as repo_submit
import repo.grades as repo_grades
import repo.files as repo_files
import logic.logging as logger
from logic.uploading import careful_upload


def submit_assignment(
    db_conn,
    db_cursor,
    course_id: str,
    assignment_id: str,
    submission_text: str,
    student_email: str,
):
    # checking constraints
    constraints.assert_student_access(db_cursor, student_email, course_id)
    constraints.assert_assignment_exists(db_cursor, course_id, assignment_id)

    submission = repo_grades.sql_select_submission_grade(db_cursor, course_id, assignment_id, student_email)

    # inserting submission
    if submission is None:
        repo_submit.sql_insert_submission(db_cursor, course_id, assignment_id, student_email, submission_text)

    # updating submission if not graded
    elif submission[0] is None:
        repo_submit.sql_update_submission_text(db_cursor, submission_text, course_id, assignment_id, student_email)

    else:
        raise HTTPException(status_code=409, detail="Can't edit the submission after it was graded.")

    logger.log(db_conn, logger.TAG_ASSIGNMENT_SUBMIT, f"Student {student_email} submitted an assignment {assignment_id} in the course {course_id}")

    return {"success": True}


def get_assignment_submissions(db_cursor, course_id: str, assignment_id: str, user_email: str):
    # checking constraints
    constraints.assert_teacher_access(db_cursor, user_email, course_id)
    constraints.assert_assignment_exists(db_cursor, course_id, assignment_id)

    # finding students' submissions
    submissions = repo_submit.sql_select_submissions(db_cursor, course_id, assignment_id)

    res = [
        {
            "course_id": course_id,
            "assignment_id": assignment_id,
            "student_email": sub[0],
            "student_name": sub[1],
            "submission_time": sub[2].strftime(TIME_FORMAT),
            "last_modification_time": sub[3].strftime(TIME_FORMAT),
            "submission_text": sub[4],
            "grade": sub[5],
            "comment": sub[6],
            "gradedby_email": sub[7],
            "gradedby_name": sub[8]
        }
        for sub in submissions
    ]
    return res


def get_submission(
    db_cursor,
    course_id: str,
    assignment_id: str,
    student_email: str,
    user_email: str,
):
    # checking constraints
    if not (
        constraints.check_teacher_access(db_cursor, user_email, course_id)
        or constraints.check_parent_student_access(db_cursor, user_email, student_email, course_id)
        or student_email == user_email
    ):
        raise HTTPException(status_code=403, detail="User does not have access to this submission")

    constraints.assert_assignment_exists(db_cursor, course_id, assignment_id)
    constraints.assert_student_access(db_cursor, student_email, course_id)

    # finding student's submission
    submission = repo_submit.sql_select_single_submission(db_cursor, course_id, assignment_id, student_email)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission of this user is not found")

    res = {
        "course_id": course_id,
        "assignment_id": assignment_id,
        "student_email": submission[0],
        "student_name": submission[1],
        "submission_time": submission[2].strftime(TIME_FORMAT),
        "last_modification_time": submission[3].strftime(TIME_FORMAT),
        "submission_text": submission[4],
        "grade": submission[5],
        "comment": submission[6],
        "gradedby_email": submission[7],
        "gradedby_name": submission[8]
    }
    return res


async def create_submission_attachment(db_conn, db_cursor, storage_db_conn, storage_db_cursor, course_id: str, assignment_id: str, student_email: str, file: UploadFile, user_email: str):
    # checking constraints
    if student_email != user_email:
        raise HTTPException(status_code=403, detail="User does not have access to this submission")

    constraints.assert_submission_exists(db_cursor, course_id, assignment_id, student_email)
    if len(file.filename) > 80:
        raise HTTPException(status_code=422, detail="File name too long")

    # read the file
    contents = await careful_upload(file)

    # save the file into database
    attachment_metadata = repo_submit.sql_insert_submission_attachment(db_cursor, storage_db_cursor, course_id, assignment_id, student_email, file.filename, contents)

    logger.log(db_conn, logger.TAG_ATTACHMENT_ADD_SUB, f"User {user_email} created an attachment {file.filename} for their submission for the assignment {assignment_id} in course {course_id}")
    return {
        "course_id": course_id,
        "assignment_id": assignment_id,
        "student_email": student_email,
        "file_id": attachment_metadata[0],
        "filename" : file.filename,
        "upload_time" : attachment_metadata[1].strftime(TIME_FORMAT)
    }


def get_submission_attachments(db_cursor, course_id: str, assignment_id: str, student_email: str, user_email: str):
    # checking constraints
    if not (
        constraints.check_teacher_access(db_cursor, user_email, course_id)
        or constraints.check_parent_student_access(db_cursor, user_email, student_email, course_id)
        or student_email == user_email
    ):
        raise HTTPException(status_code=403, detail="User does not have access to this submission")

    constraints.assert_submission_exists(db_cursor, course_id, assignment_id, student_email)

    # searching for submission attachments
    files = repo_submit.sql_select_submission_attachments(db_cursor, course_id, assignment_id, student_email)

    res = [{
        "course_id": course_id,
        "assignment_id": assignment_id,
        "student_email": student_email,
        "file_id": file[0],
        "filename": file[1],
        "upload_time": file[2].strftime(TIME_FORMAT)
    } for file in files]

    return res


def download_submission_attachment(db_cursor, storage_db_cursor, course_id: str, assignment_id: str, student_email: str, file_id: str, user_email: str):
    # checking constraints
    if not (
        constraints.check_teacher_access(db_cursor, user_email, course_id)
        or constraints.check_parent_student_access(db_cursor, user_email, student_email, course_id)
        or student_email == user_email
    ):
        raise HTTPException(status_code=403, detail="User does not have access to this submission")

    constraints.assert_submission_exists(db_cursor, course_id, assignment_id, student_email)

    # searching for submission attachment
    file = repo_files.sql_download_attachment(storage_db_cursor, file_id)
    file_metadata = repo_files.sql_select_attachment_metadata(db_cursor, file_id)
    if (not file or not file_metadata):
        raise HTTPException(status_code=404, detail="Attachment not found")

    return Response(
        content=file,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_metadata[1]}"'}
    )
