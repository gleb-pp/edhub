from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.auth import get_current_user
from src.db import get_db
from src.exceptions import courses as course_errors
from src.exceptions import students as student_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.models.users import User
from src.policies import CoursePolicy, ParentPolicy, StudentPolicy, TeacherPolicy
from src.services import (
    CourseService,
    PersonalizationService,
    StudentService,
    UserService,
)

router = APIRouter(
    prefix="/courses/{course_id}",
    tags=["Students"],
)


@router.get("/students")
async def get_enrolled_students(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user),
) -> list[User]:
    """
    Get the list of enrolled students by course_id.

    Students are sorted in the alphabetical order (first by user name, then by email).

    Return the email and name of each student.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    student_service = StudentService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        if not user.isadmin:
            CoursePolicy.assert_course_access(user, course, db)
        students = student_service.get_enrolled_students(course)
        return [User.model_validate(st) for st in students]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/students")
async def invite_student(
    course_id: str,
    student_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Add the student with provided email to the course with provided course_id.

    Teacher OR Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    student_service = StudentService(db)
    personalization_service = PersonalizationService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        student = user_service.get_user(student_email)
        StudentPolicy.assert_not_student(student, course, db)
        TeacherPolicy.assert_not_teacher(student, course, db)
        ParentPolicy.assert_not_parent(student, course, db)
        student_service.invite_student(student, course)
        personalization_service.add_course_participant(course, student)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        elif e.email == student_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.RoleConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.delete("/students/{student_email}")
async def remove_student(
    course_id: str,
    student_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Remove the student with provided email from the course with provided course_id.

    All the student's submissions will be deleted.

    Teacher OR Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    student_service = StudentService(db)
    personalization_service = PersonalizationService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        student = user_service.get_user(student_email)
        StudentPolicy.assert_student_access(student, course, db)
        student_service.remove_student(student, course)
        personalization_service.remove_course_participant(course, student)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        elif e.email == student_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except student_errors.StudentRoleRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
