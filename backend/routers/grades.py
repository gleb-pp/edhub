from fastapi import APIRouter, Depends, Query, HTTPException
from auth import get_current_user
from models.common import Success
from models.grades import StudentsGrades, AssignmentGrade
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
        min_length=3,
        max_length=10000,
        description="Comment must contain 3-10000 symbols"
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


@router.get("/")
async def get_all_course_grades(
    course_id: str,
    user_email: str = Depends(get_current_user)
) -> list[StudentsGrades]:
    """
    Get the table of all course grades.

    Returns the list where each row corresponds to some student (students are sorted in the alphabetical order (first by user name, then by email)).

    Each row has the following format: {name: str, email: str, grades: List[int | None]}

    Students (rows) are ordered by user name, then by email.

    Assignments (grades) are ordered by section_order, then by creation_date, old posts go first.

    Grades list can contain `null` values if the assignment was not graded yet.

    Teacher OR Primary Instructor role required.
    """

    # connection to database
    with get_db() as (db_conn, db_cursor):
        return logic.grades.get_all_course_grades(db_cursor, course_id, user_email)


@router.get("/{student_email}")
async def get_student_course_grades(
    course_id: str,
    student_email: str,
    user_email: str = Depends(get_current_user)
) -> list[AssignmentGrade]:
    """
    Get the table of course grades of student with provided student_email.

    - Teacher OR Primary Instructor can get grades of every student.
    - Parent can get the grades of their student
    - Student can get their grades

    Returns the list where each row corresponds to some assignment.

    Each row has the following format: {assignment_name: str, assignment_id: int, grade: int | None, comment: str | None, grader_name: str | None, grader_email: str | None}

    Assignments are ordered by section_order, then by creation_date, old posts go first.

    `grade`, `comment`, `grader_name`, and `grader_email` can be `null` if the assignment was not graded yet.
    """

    # connection to database
    with get_db() as (db_conn, db_cursor):
        return logic.grades.get_student_course_grades(db_cursor, course_id, student_email, user_email)
