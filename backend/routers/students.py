from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
import logic.students
from models.common import Success
from models.users import User
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
import logic.users as user_logic
import exceptions.users as user_errors
import logic.courses as course_logic
import exceptions.courses as course_errors
import logic.students as student_logic

router = APIRouter(
    prefix='/{course_id}/students',
    tags=["Courses"],
)


@router.get("/")
async def get_enrolled_students(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user)
) -> list[User]:
    """
    Get the list of enrolled students by course_id.

    Students are sorted in the alphabetical order (first by user name, then by email).

    Return the email and name of each student.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        course_logic.assert_course_access(user, course, db)
        students = student_logic.get_enrolled_students(course, db)
        return [User.model_validate(st) for st in students]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/")
async def invite_student(
    course_id: str,
    student_email: str,
    teacher_email: str = Depends(get_current_user)
) -> Success:
    """
    Add the student with provided email to the course with provided course_id.

    Teacher OR Primary Instructor role required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.students.invite_student(db_conn, db_cursor, course_id, student_email, teacher_email)


@router.delete("/{student_email}")
async def remove_student(
    course_id: str,
    student_email: str,
    user_email: str = Depends(get_current_user)
) -> Success:
    """
    Remove the student with provided email from the course with provided course_id.

    Teacher OR Primary Instructor OR Student role required.

    Student can only remove themselves.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.students.remove_student(db_conn, db_cursor, course_id, student_email, user_email)
