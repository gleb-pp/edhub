from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from auth import get_current_user, get_db
import json_classes
import logic.grades


router = APIRouter()


@router.put("/grade_submission", response_model=json_classes.Success, tags=["Grades"])
async def grade_submission(
    course_id: str,
    assignment_id: str,
    student_email: str,
    grade: int,
    comment: Optional[str] = Query(
        None,
        min_length=3,
        max_length=10000,
        description="Comment must contain 3-10000 symbols"
    ),
    user_email: str = Depends(get_current_user),
):
    """
    Allows teacher to grade student's submission.

    If the assignment is already graded, the grade will be updated.

    Teacher OR Primary Instructor role required.

    Comment must be None or contain from 3 to 10000 symbols.
    """

    # connection to database
    with get_db() as (db_conn, db_cursor):
        return logic.grades.grade_submission(
            db_conn,
            db_cursor,
            course_id,
            assignment_id,
            student_email,
            grade,
            comment,
            user_email
        )


@router.get("/get_all_course_grades", response_model=List[json_classes.StudentsGrades], tags=["Grades"])
async def get_all_course_grades(
    course_id: str,
    user_email: str = Depends(get_current_user)
):
    """
    Get the table of all course grades.

    Teacher OR Primary Instructor role required.

    Returns the list where each row corresponds to some student (students are sorted in the alphabetical order (first by user name, then by email)).

    Each row has the following format: {name: str, email: str, grades: List[Optional[int]]}

    Students (rows) are ordered by user name, then by email.

    Assignments (grades) are ordered by section_order, then by creation_date, old posts go first.

    Grades list can contain `null` values if the assignment was not graded yet.
    """

    # connection to database
    with get_db() as (db_conn, db_cursor):
        return logic.grades.get_all_course_grades(db_cursor, course_id, user_email)


@router.get("/get_student_course_grades", response_model=List[json_classes.AssignmentGrade], tags=["Grades"])
async def get_student_course_grades(
    course_id: str,
    student_email: str,
    user_email: str = Depends(get_current_user)
):
    """
    Get the table of course grades of student with provided student_email.

    - Teacher OR Primary Instructor can get grades of every student.
    - Parent can get the grades of their student
    - Student can get their grades

    Returns the list where each row corresponds to some assignment.

    Each row has the following format: {assignment_name: str, assignment_id: int, grade: Optional[int], comment: Optional[str], grader_name: Optional[str], grader_email: Optional[str]}

    Assignments are ordered by section_order, then by creation_date, old posts go first.

    `grade`, `comment`, `grader_name`, and `grader_email` can be `null` if the assignment was not graded yet.
    """

    # connection to database
    with get_db() as (db_conn, db_cursor):
        return logic.grades.get_student_course_grades(db_cursor, course_id, student_email, user_email)
