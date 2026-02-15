from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.auth import get_current_user
from src.db import get_db
from src.exceptions import assignments as assignment_errors
from src.exceptions import courses as course_errors
from src.exceptions import students as student_errors
from src.exceptions import submissions as submission_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.models.submissions import Submission
from src.policies import GradePolicy, StudentPolicy, TeacherPolicy
from src.services import (
    AssignmentService,
    CourseService,
    SubmissionService,
    UserService,
)

router = APIRouter(
    prefix="/courses/{course_id}/assignments/{assignment_id}",
    tags=["Submissions"],
)


@router.put("/submissions")
async def submit_assignment(
    course_id: str,
    assignment_id: int,
    db: Annotated[Session, Depends(get_db)],
    submission_text: Annotated[str, Query(
        ...,
        min_length=3,
        max_length=10000,
        description="Submission text must contain 3-10000 symbols",
    )],
    student_email: Annotated[str, Depends(get_current_user)],
) -> Success:
    """
    Allow student to submit their assignment OR edit their submission.

    Submission text must contains from 3 to 10000 symbols.

    Student role required.

    Student cannot submit already graded assignment.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    assignment_service = AssignmentService(db)
    submission_service = SubmissionService(db)
    try:
        student = user_service.get_user(student_email)
        course = course_service.get_course(course_id)
        StudentPolicy.assert_student_access(student, course, db)
        assignment = assignment_service.get_assignment(course, assignment_id)
        submission = submission_service.get_submission(assignment, student)
        GradePolicy.assert_not_graded(submission, db)
        submission_service.update_submission(submission, submission_text)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        assignment_errors.AssignmentNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except student_errors.StudentRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except submission_errors.SubmissionGradedError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except submission_errors.SubmissionNotFoundError:
        submission_service.create_submission(assignment, student, submission_text)
        db.commit()
        return Success(success=True)


@router.get("/submissions")
async def get_assignment_submissions(
    course_id: str,
    assignment_id: int,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: Annotated[str, Depends(get_current_user)],
) -> list[Submission]:
    """
    Get the list of students submissions for the provided assignment.

    Each submission has the form of (course_id, assignment_id, email, timeadded, timemodified, and submission_text).

    Submissions are ordered by submission_time, newest submissions go first.

    Teacher OR Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    assignment_service = AssignmentService(db)
    submission_service = SubmissionService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        assignment = assignment_service.get_assignment(course, assignment_id)
        submissions = submission_service.get_assignment_submissions(assignment)
        return [Submission.model_validate(sub) for sub in submissions]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        assignment_errors.AssignmentNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/submissions/{student_email}")
async def get_submission(
    course_id: str,
    assignment_id: int,
    student_email: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: Annotated[str, Depends(get_current_user)],
) -> Submission:
    """
    Get the student submission of assignment by course_id, assignment_id and student_email.

    - Teacher OR Primary Instructor can get all submissions of the course
    - Parent can get the submission of their student
    - Student can get their submissions

    Returns the submission (course_id, assignment_id, email, timeadded, timemodified, and submission_text).
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    assignment_service = AssignmentService(db)
    submission_service = SubmissionService(db)
    try:
        user = user_service.get_user(user_email)
        student = user_service.get_user(student_email)
        course = course_service.get_course(course_id)
        StudentPolicy.assert_access_to_student(student, user, course, db)
        assignment = assignment_service.get_assignment(course, assignment_id)
        submission = submission_service.get_submission(assignment, student)
        return Submission.model_validate(submission)
    except user_errors.UserNotFoundError as e:
        if e.email == user_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        student_errors.StudentRoleRequiredError,
        assignment_errors.AssignmentNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except submission_errors.SubmissionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (
        course_errors.ParticipantRoleRequiredError,
        student_errors.NoAccessToStudentInfoError,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


# @router.post("/{student_email}/attachment")
# async def create_submission_attachment(
#     course_id: str,
#     assignment_id: str,
#     student_email: str,
#     file: UploadFile = File(...),
#     user_email: Annotated[str, Depends(get_current_user)],
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
#     user_email: Annotated[str, Depends(get_current_user)]
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
#     user_email: Annotated[str, Depends(get_current_user)]
# ):
#     """
#     Download the attachment to the course assignment submission by provided course_id, assignment_id, student_email, file_id.
#     """
#     with get_db() as (db_conn, db_cursor), get_storage_db() as (storage_db_conn, storage_db_cursor):
#         return logic.submissions.download_submission_attachment(db_cursor, storage_db_cursor, course_id, assignment_id, student_email, file_id, user_email)
