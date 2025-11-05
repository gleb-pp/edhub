from fastapi import APIRouter, Depends
from auth import get_current_user, get_db
import logic.students
from models.common import Success
from models.users import User


router = APIRouter(
    prefix='/{course_id}/students',
    tags=["Courses"],
)


@router.get("/")
async def get_enrolled_students(
    course_id: str,
    user_email: str = Depends(get_current_user)
) -> list[User]:
    """
    Get the list of enrolled students by course_id.

    Students are sorted in the alphabetical order (first by user name, then by email).

    Return the email and name of each student.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    with get_db() as (db_conn, db_cursor):
        return logic.students.get_enrolled_students(db_cursor, course_id, user_email)


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
