from fastapi import APIRouter, Query, Depends, HTTPException
from src.auth import get_current_user
from src.models.courses import CourseID, Course
from src.models.common import Success
from typing import Annotated
from sqlalchemy.orm import Session
from src.db import get_db
from src.services import (
    UserService,
    CourseService,
    PersonalizationService,
    SectionService,
    StudentService,
    TeacherService,
    ParentService,
)
from src.policies import TeacherPolicy, CoursePolicy, StudentPolicy, ParentPolicy
from src.exceptions import (
    teachers as teacher_errors,
    courses as course_errors,
    users as user_errors,
)
from src.settings.course import course_settings

router = APIRouter(
    tags=["Courses"],
)


@router.get("/courses")
async def get_available_courses(
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> list[Course]:
    """
    Get the list of of courses available for user (as a Primary Instructor, Teacher, Student, or Parent).

    For each course, returns (course_id, title, organization, instructor_email, and creation_time).
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    try:
        user = user_service.get_user(user_email)
        courses = course_service.get_available_courses(user)
        return [Course.model_validate(course) for course in courses]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.post("/courses")
async def create_course(
    db: Annotated[Session, Depends(get_db)],
    title: str = Query(
        ...,
        min_length=course_settings.name_min_lenght,
        max_length=course_settings.name_max_lenght,
        pattern=r"^[\p{L}0-9_ ]+$",
        description=f"Title can contain only letters, digits, spaces, and underscores, {course_settings.name_min_lenght}-{course_settings.name_max_lenght} symbols",
    ),
    organization: str | None = Query(
        None,
        min_length=course_settings.organization_min_lenght,
        max_length=course_settings.organization_max_lenght,
        pattern=r"^[\p{L}0-9_ ]+$",
        description=f"Organization can contain only letters, digits, spaces, and underscores, {course_settings.organization_min_lenght}-{course_settings.organization_max_lenght} symbols",
    ),
    user_email: str = Depends(get_current_user),
) -> CourseID:
    """
    Create the course with provided title and become a Primary Instructor in it.

    Title and Organization can contain only letters, digits, spaces, and underscores.

    Title and Organization must contains from 3 to 80 symbols.

    Organization parameter is optional / can be None.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    personalization_service = PersonalizationService(db)
    section_service = SectionService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.create_course(title, organization, user)
        personalization_service.add_course_participant(course, user)
        section_service.create_section("General", course)
        db.commit()
        return CourseID.model_validate(course)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> Success:
    """
    Remove the course with provided course_id.

    All the course materials, teachers, students, and parents will be also removed.

    Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if not user.isadmin:
            TeacherPolicy.assert_instructor_access(user, course, db)
        course_service.delete_course(course)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except teacher_errors.InstructorRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/courses/{course_id}")
async def get_course_info(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> Course:
    """
    Get information about the course: course_id, title, organization, instructor_email, and creation_time.

    Organization can be None.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if not user.isadmin:
            CoursePolicy.assert_course_access(user, course, db)
        return Course.model_validate(course)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/courses/{course_id}/leave")
async def leave_course(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> Success:
    """
    Remove user from the course with provided course_id.

    If the user is student, all their submissions will be deleted.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    student_service = StudentService(db)
    teacher_service = TeacherService(db)
    parent_service = ParentService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if StudentPolicy.check_student_access(user, course, db):
            student_service.remove_student(user, course)
            db.commit()
            return Success(success=True)
        if TeacherPolicy.check_teacher_access(user, course, db):
            teacher_service.remove_teacher(user, course)
            db.commit()
            return Success(success=True)
        if ParentPolicy.check_parent_access(user, course, db):
            parent_service.remove_parent(user, course)
            db.commit()
            return Success(success=True)
        if TeacherPolicy.check_instructor_access(user, course, db):
            raise teacher_errors.DeleteInstructorError(user.email, course.course_id)
        raise course_errors.ParticipantRoleRequired(user.email, course_id)
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        teacher_errors.DeleteInstructorError,
        course_errors.ParticipantRoleRequired,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
