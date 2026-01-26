from fastapi import APIRouter, Depends, Query, HTTPException
from auth import get_current_user
from models.common import Success
from models.grades import AssignmentGrade
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
from services import (
    CourseService,
    UserService,
    GradeService,
    AssignmentService,
    SubmissionService,
)
from policies import TeacherPolicy, StudentPolicy
from exceptions import (
    users as user_errors,
    courses as course_errors,
    students as student_errors,
    teachers as teacher_errors,
    assignments as assignment_errors,
    submissions as submission_errors,
)
from settings.submissions import submission_settings

router = APIRouter(
    prefix="/{course_id}/grades",
    tags=["Grades"],
)


@router.put("/{assignment_id}/{student_email}")
async def grade_submission(
    course_id: str,
    assignment_id: int,
    student_email: str,
    grade: int,
    db: Annotated[Session, Depends(get_db)],
    comment: str | None = Query(
        None,
        min_length=submission_settings.grade_comment_min_lenght,
        max_length=submission_settings.grade_comment_max_lenght,
        description=f"Comment must contain {submission_settings.grade_comment_min_lenght}-{submission_settings.grade_comment_max_lenght} symbols",
    ),
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Allows teacher to grade student's submission.

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
        elif e.email == student_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        student_errors.StudentRoleRequired,
        assignment_errors.AssignmentNotFoundError,
        submission_errors.SubmissionNotFoundError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/{assignment_id}/{student_email}")
async def get_submission_grade(
    course_id: str,
    assignment_id: int,
    student_email: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
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
        else:
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
        course_errors.ParticipantRoleRequired,
        student_errors.StudentRoleRequired,
        student_errors.NoAccessToStudentInfo,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
