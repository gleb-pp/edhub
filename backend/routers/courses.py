from fastapi import APIRouter, Query, Depends, HTTPException
from auth import get_current_user
from models.courses import CourseID, Course
from models.common import Success
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
import logic.users as user_logic
import logic.courses as course_logic
import logic.teachers as teacher_logic
import exceptions.teachers as teacher_errors
import exceptions.courses as course_errors
import exceptions.users as user_errors
import logic.personalization as personalization_logic
import logic.sections as section_logic
import logic.students as student_logic
import logic.parents as parent_logic


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


@router.get("/")
async def get_available_courses(
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> list[Course]:
    """
    Get the list of of courses available for user (as a Primary Instructor, Teacher, Student, or Parent).

    For each course, returns (course_id, title, organization, instructor_email, and creation_time).
    """
    try:
        user = user_logic.get_user(user_email, db)
        courses = course_logic.get_available_courses(user, db)
        return [Course.model_validate(course) for course in courses]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.post("/")
async def create_course(
    db: Annotated[Session, Depends(get_db)],
    title: str = Query(
        ...,
        min_length=3,
        max_length=80,
        pattern=r"^[\p{L}0-9_ ]+$",
        description="Title can contain only letters, digits, spaces, and underscores, 3-80 symbols"
    ),
    organization: str | None = Query(
        None,
        min_length=3,
        max_length=80,
        pattern=r"^[\p{L}0-9_ ]+$",
        description="Organization can contain only letters, digits, spaces, and underscores, 3-80 symbols"
    ),
    user_email: str = Depends(get_current_user),
) -> CourseID:
    """
    Create the course with provided title and become a Primary Instructor in it.

    Title and Organization can contain only letters, digits, spaces, and underscores.

    Title and Organization must contains from 3 to 80 symbols.

    Organization parameter is optional / can be None.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.create_course(title, organization, user, db)
        personalization_logic.add_course_participant(course, user, db)
        section_logic.create_section("General", course, db)
        db.commit()
        return CourseID.model_validate(course)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.delete("/{course_id}")
async def delete_course(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user)
) -> Success:
    """
    Remove the course with provided course_id.

    All the course materials, teachers, students, and parents will be also removed.

    Primary Instructor role required.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_instructor_access(user, course, db)
        course_logic.delete_course(course, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except teacher_errors.InstructorRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{course_id}")
async def get_course_info(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user)
) -> Course:
    """
    Get information about the course: course_id, title, organization, instructor_email, and creation_time.

    Organization can be None.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        course_logic.assert_course_access(user, course, db)
        return Course.model_validate(course)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{course_id}/exit")
async def exit_course(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user)
) -> Success:
    """
    Remove user from the course with provided course_id.

    If the user is student, all their submissions will be deleted.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        if student_logic.check_student_access(user, course, db):
            student_logic.remove_student(user, course, db)
            db.commit()
            return Success(success=True)
        if teacher_logic.check_teacher_access(user, course, db):
            teacher_logic.remove_teacher(user, course, db)
            db.commit()
            return Success(success=True)
        if parent_logic.check_parent_access(user, course, db):
            parent_logic.remove_parent(user, course, db)
            db.commit()
            return Success(success=True)
        if teacher_logic.check_instructor_access(user, course, db):
            raise teacher_errors.DeleteInstructorError(user.email, course.course_id)
        raise course_errors.ParticipantRoleRequired(user.email, course_id)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        teacher_errors.DeleteInstructorError,
        course_errors.ParticipantRoleRequired
    ):
        raise HTTPException(status_code=403, detail=str(e)) from e
