from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from auth import get_current_user
from models.common import Success
from models.submissions import Submission, SubmissionAttachmentMetadata
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
import logic.users as user_logic
import exceptions.users as user_errors
import logic.courses as course_logic
import exceptions.courses as course_errors
import logic.students as student_logic
import exceptions.students as student_errors
import logic.teachers as teacher_logic
import exceptions.teachers as teacher_errors
import logic.assignments as assignment_logic
import exceptions.assignments as assignment_errors
import logic.submissions as submission_logic
import exceptions.submissions as submission_errors
import logic.grades as grade_logic

router = APIRouter(
    prefix='/{course_id}/{assignment_id}/submissions',
    tags=["Submissions"],
)


@router.put("/")
async def submit_assignment(
    course_id: str,
    assignment_id: int,
    db: Annotated[Session, Depends(get_db)],
    submission_text: str = Query(
        ...,
        min_length=3,
        max_length=10000,
        description="Submission text must contain 3-10000 symbols"
    ),
    student_email: str = Depends(get_current_user),
) -> Success:
    """
    Allows student to submit their assignment OR edit their submission.

    Submission text must contains from 3 to 10000 symbols.

    Student role required.

    Student cannot submit already graded assignment.
    """
    try:
        student = user_logic.get_user(student_email, db)
        course = course_logic.get_course(course_id, db)
        student_logic.assert_student_access(student, course, db)
        assignment = assignment_logic.get_assignment(course, assignment_id, db)
        submission = submission_logic.get_submission(assignment, student, db)
        grade_logic.assert_not_graded(submission, db)
        submission_logic.update_submission(submission, submission_text)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        assignment_errors.AssignmentNotFoundError
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except student_errors.StudentRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except submission_errors.SubmissionGradedError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except submission_errors.SubmissionNotFoundError:
        submission_logic.create_submission(assignment, student, submission_text, db)
        db.commit()
        return Success(success=True)


@router.get("/")
async def get_assignment_submissions(
    course_id: str,
    assignment_id: int,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user)
) -> list[Submission]:
    """
    Get the list of students submissions for the provided assignment.

    Each submission has the form of (course_id, assignment_id, email, timeadded, timemodified, and submission_text).

    Submissions are ordered by submission_time, newest submissions go first.

    Teacher OR Primary Instructor role required.
    """
    try:
        teacher = user_logic.get_user(teacher_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_teacher_access(teacher, course, db)
        assignment = assignment_logic.get_assignment(course, assignment_id, db)
        submissions = submission_logic.get_assignment_submissions(assignment, db)
        return [Submission.model_validate(sub) for sub in submissions]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        assignment_errors.AssignmentNotFoundError
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/{student_email}")
async def get_submission(
    course_id: str,
    assignment_id: int,
    student_email: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> Submission:
    """
    Get the student submission of assignment by course_id, assignment_id and student_email.

    - Teacher OR Primary Instructor can get all submissions of the course
    - Parent can get the submission of their student
    - Student can get their submissions

    Returns the submission (course_id, assignment_id, email, timeadded, timemodified, and submission_text).
    """
    try:
        user = user_logic.get_user(user_email, db)
        student = user_logic.get_user(student_email, db)
        course = course_logic.get_course(course_id, db)
        student_logic.assert_access_to_student(student, user, course, db)
        assignment = assignment_logic.get_assignment(course, assignment_id, db)
        submission = submission_logic.get_submission(assignment, student, db)
        return Submission.model_validate(submission)
    except user_errors.UserNotFoundError as e:
        if e.email == user_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        assignment_errors.AssignmentNotFoundError
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except submission_errors.SubmissionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (
        course_errors.ParticipantRoleRequired,
        student_errors.StudentRoleRequired,
        student_errors.NoAccessToStudentInfo,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


# @router.post("/{student_email}/attachment")
# async def create_submission_attachment(
#     course_id: str,
#     assignment_id: str,
#     student_email: str,
#     file: UploadFile = File(...),
#     user_email: str = Depends(get_current_user),
# ) -> SubmissionAttachmentMetadata:
#     """
#     Attach the provided file to provided course assignment submission.

#     Filename should contain no more than 80 symbols.

#     Student role required.

#     Returns the (course_id, assignment_id, student_email, file_id, filename, upload_time) for the new attachment in case of success.

#     The format of upload_time is TIME_FORMAT.
#     """
#     with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
#         return await logic.submissions.create_submission_attachment(db_conn, db_cursor, storage_db_conn, storage_db_cursor, course_id, assignment_id, student_email, file, user_email)


# @router.get("/{student_email}/attachment")
# async def get_submission_attachments(
#     course_id: str,
#     assignment_id: str,
#     student_email: str,
#     user_email: str = Depends(get_current_user)
# ) -> list[SubmissionAttachmentMetadata]:
#     """
#     Get the list of attachments to the course assignment submission by provided course_id, assignment_id, student_email.

#     - Teacher OR Primary Instructor can get all submission attachments of the course
#     - Parent can get the submission attachments of their student
#     - Student can get their submission attachments

#     Returns list of attachments metadata (course_id, assignment_id, student_email, file_id, filename, upload_time).

#     The format of upload_time is TIME_FORMAT.
#     """
#     with get_db() as (db_conn, db_cursor):
#         return logic.submissions.get_submission_attachments(db_cursor, course_id, assignment_id, student_email, user_email)


# @router.get("/{student_email}/attachment/{file_id}")
# async def download_submission_attachment(
#     course_id: str,
#     assignment_id: str,
#     student_email: str,
#     file_id: str,
#     user_email: str = Depends(get_current_user)
# ):
#     """
#     Download the attachment to the course assignment submission by provided course_id, assignment_id, student_email, file_id.
#     """
#     with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
#         return logic.submissions.download_submission_attachment(db_cursor, storage_db_cursor, course_id, assignment_id, student_email, file_id, user_email)
