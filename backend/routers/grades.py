from fastapi import APIRouter, Depends, Query, HTTPException
from auth import get_current_user
from models.common import Success
from models.grades import AssignmentGrade
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
import services.users as user_logic
import exceptions.users as user_errors
import services.courses as course_logic
import exceptions.courses as course_errors
import services.students as student_logic
import exceptions.students as student_errors
import services.teachers as teacher_logic
import exceptions.teachers as teacher_errors
import services.assignments as assignment_logic
import exceptions.assignments as assignment_errors
import services.submissions as submission_logic
import exceptions.submissions as submission_errors
import services.grades as grade_logic
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
        description=f"Comment must contain {submission_settings.grade_comment_min_lenght}-{submission_settings.grade_comment_max_lenght} symbols"
    ),
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Allows teacher to grade student's submission.

    If the assignment is already graded, the grade will be updated.

    Teacher OR Primary Instructor role required.

    Comment must be None or contain from 3 to 10000 symbols.
    """
    try:
        teacher = user_logic.get_user(teacher_email, db)
        course = course_logic.get_course(course_id, db)
        if not teacher.isadmin:
            teacher_logic.assert_teacher_access(teacher, course, db)
        student = user_logic.get_user(student_email, db)
        student_logic.assert_student_access(student, course, db)
        assignment = assignment_logic.get_assignment(course, assignment_id, db)
        submission = submission_logic.get_submission(assignment, student, db)
        grade_logic.update_submission_grade(submission, grade, comment, teacher, db)
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
        submission_errors.SubmissionNotFoundError
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
    try:
        user = user_logic.get_user(user_email, db)
        student = user_logic.get_user(student_email, db)
        course = course_logic.get_course(course_id, db)
        student_logic.assert_access_to_student(student, user, course, db)
        assignment = assignment_logic.get_assignment(course, assignment_id, db)
        submission = submission_logic.get_submission(assignment, student, db)
        grade = grade_logic.get_submission_grade(submission, db)
        return AssignmentGrade.model_validate(grade)
    except user_errors.UserNotFoundError as e:
        if e.email == user_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        assignment_errors.AssignmentNotFoundError,
        submission_errors.SubmissionNotFoundError
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
