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
from src.models.grades import AssignmentGrade
from src.policies import StudentPolicy, TeacherPolicy
from src.services import (
    AssignmentService,
    CourseService,
    GradeService,
    SubmissionService,
    UserService,
)
from src.settings.submissions import submission_settings

router = APIRouter(
    prefix="/courses/{course_id}/assignments/{assignment_id}/submissions/{student_email}",
    tags=["Grades"],
)


@router.put("/grade")
async def grade_submission(
    course_id: str,
    assignment_id: int,
    student_email: str,
    grade: int,
    db: Annotated[Session, Depends(get_db)],
    comment: Annotated[str | None, Query(
        None,
        min_length=submission_settings.grade_comment_min_lenght,
        max_length=submission_settings.grade_comment_max_lenght,
        description=f"Comment must contain {submission_settings.grade_comment_min_lenght}-{submission_settings.grade_comment_max_lenght} symbols",
    )],
    teacher_email: Annotated[str, Depends(get_current_user)],
) -> Success:
    """
    Allow teacher to grade student's submission.

    If the assignment is already graded, the grade will be updated.

    Teacher OR Primary Instructor role required.

    Comment must be None or contain from 3 to 10000 symbols.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    assignment_service = AssignmentService(db)
    submission_service = SubmissionService(db)
    grade_service = GradeService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        student = user_service.get_user(student_email)
        StudentPolicy.assert_student_access(student, course, db)
        assignment = assignment_service.get_assignment(course, assignment_id)
        submission = submission_service.get_submission(assignment, student)
        grade_service.update_submission_grade(submission, grade, comment, teacher)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        if e.email == student_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        student_errors.StudentRoleRequiredError,
        assignment_errors.AssignmentNotFoundError,
        submission_errors.SubmissionNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/grade")
async def get_submission_grade(
    course_id: str,
    assignment_id: int,
    student_email: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: Annotated[str, Depends(get_current_user)],
) -> AssignmentGrade:
    """
    Get the grade for the student's submission.

    Returns (course_id, assignment_id, student_email, grade, comment, teacher_email, and time_graded).

    - Teacher OR Primary Instructor can get the grades for all submissions
    - Parent can get the grades for submissions of their children
    - Student can get the grade for their submision
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    assignment_service = AssignmentService(db)
    submission_service = SubmissionService(db)
    grade_service = GradeService(db)
    try:
        user = user_service.get_user(user_email)
        student = user_service.get_user(student_email)
        course = course_service.get_course(course_id)
        StudentPolicy.assert_access_to_student(student, user, course, db)
        assignment = assignment_service.get_assignment(course, assignment_id)
        submission = submission_service.get_submission(assignment, student)
        grade = grade_service.get_submission_grade(submission)
        return AssignmentGrade.model_validate(grade)
    except user_errors.UserNotFoundError as e:
        if e.email == user_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        assignment_errors.AssignmentNotFoundError,
        submission_errors.SubmissionNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except submission_errors.GradeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (
        course_errors.ParticipantRoleRequiredError,
        student_errors.StudentRoleRequiredError,
        student_errors.NoAccessToStudentInfoError,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
