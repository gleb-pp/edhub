from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.auth import get_current_user
from src.db import get_db
from src.exceptions import courses as course_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.models.users import User
from src.policies import CoursePolicy, ParentPolicy, StudentPolicy, TeacherPolicy
from src.services import (
    CourseService,
    PersonalizationService,
    TeacherService,
    UserService,
)

router = APIRouter(
    prefix="/courses/{course_id}",
    tags=["Teachers"],
)


@router.get("/teachers")
async def get_course_teachers(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: Annotated[str, Depends(get_current_user)],
) -> list[User]:
    """
    Get the list of teachers teaching the course with the provided course_id.

    Does NOT return the Primary Instructor.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    teacher_service = TeacherService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if not user.is_admin:
            CoursePolicy.assert_course_access(user, course, db)
        teachers = teacher_service.get_course_teachers(course)
        return [User.model_validate(tchr) for tchr in teachers]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/teachers")
async def invite_teacher(
    course_id: str,
    new_teacher_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: Annotated[str, Depends(get_current_user)],
) -> Success:
    """
    Add the user with provided new_teacher_email as a teacher to the course with provided course_id.

    Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    teacher_service = TeacherService(db)
    try:
        personalization_service = PersonalizationService(db)
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.is_admin:
            TeacherPolicy.assert_instructor_access(teacher, course)
        new_teacher = user_service.get_user(new_teacher_email)
        TeacherPolicy.assert_not_teacher(new_teacher, course, db)
        StudentPolicy.assert_not_student(new_teacher, course, db)
        ParentPolicy.assert_not_parent(new_teacher, course, db)
        teacher_service.invite_teacher(new_teacher, course)
        personalization_service.add_course_participant(course, new_teacher)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        if e.email == new_teacher_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.InstructorRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.RoleConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.delete("/teachers/{removing_teacher_email}")
async def remove_teacher(
    course_id: str,
    removing_teacher_email: str,
    db: Annotated[Session, Depends(get_db)],
    instructor_email: Annotated[str, Depends(get_current_user)],
) -> Success:
    """
    Remove the teacher with removing_teacher_email from the course with provided course_id.

    Primary Instructor role required.

    Primary Instructor can't remove themself until they are Primary Instructor.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    teacher_service = TeacherService(db)
    personalization_service = PersonalizationService(db)
    try:
        instructor = user_service.get_user(instructor_email)
        course = course_service.get_course(course_id)
        if instructor.is_admin:
            instructor = user_service.get_user(course.instructor)
        else:
            TeacherPolicy.assert_instructor_access(instructor, course)
        teacher = user_service.get_user(removing_teacher_email)
        TeacherPolicy.assert_teacher_access(teacher, course, db)
        teacher_service.remove_teacher(teacher, course)
        personalization_service.remove_course_participant(course, teacher)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == instructor_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.InstructorRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.patch("/teachers/instructor", tags=["Courses"])
async def change_course_instructor(
    course_id: str,
    teacher_email: str,
    db: Annotated[Session, Depends(get_db)],
    instructor_email: Annotated[str, Depends(get_current_user)],
) -> Success:
    """
    Transfer the course ownership (Primary Instructor role) to other Teacher within the course.

    Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    teacher_service = TeacherService(db)
    try:
        instructor = user_service.get_user(instructor_email)
        course = course_service.get_course(course_id)
        TeacherPolicy.assert_instructor_access(instructor, course)
        teacher = user_service.get_user(teacher_email)
        TeacherPolicy.assert_teacher_access(teacher, course, db)
        teacher_service.change_course_instructor(instructor, teacher, course)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == instructor_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        if e.email == teacher_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.InstructorRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
