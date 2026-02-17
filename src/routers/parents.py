from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.auth import get_current_user
from src.db import get_db
from src.exceptions import courses as course_errors
from src.exceptions import parents as parent_errors
from src.exceptions import students as student_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.models.users import User
from src.policies import ParentPolicy, StudentPolicy, TeacherPolicy
from src.services import (
    CourseService,
    ParentService,
    PersonalizationService,
    UserService,
)

router = APIRouter(
    prefix="/courses/{course_id}",
    tags=["Parents"],
)


@router.get("/students/{student_email}/parents")
async def get_students_parents(
    course_id: str,
    student_email: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: Annotated[str, Depends(get_current_user)],
) -> list[User]:
    """
    Get the list of parents observing the student with provided email on course with provided course_id.

    - Teacher OR Primary Instructor can get the list of parents for all students
    - Parent can get the list of parents for their children
    - Student can get the list of their parents
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    parent_service = ParentService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        student = user_service.get_user(student_email)
        StudentPolicy.assert_access_to_student(student, user, course, db)
        parents = parent_service.get_students_parents(student, course)
        return [User.model_validate(par) for par in parents]
    except user_errors.UserNotFoundError as e:
        if e.email == user_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (course_errors.CourseNotFoundError, student_errors.StudentRoleRequiredError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.ParticipantRoleRequiredError,
        student_errors.NoAccessToStudentInfoError,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/students/{student_email}/parents")
async def invite_parent(
    course_id: str,
    student_email: str,
    parent_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: Annotated[str, Depends(get_current_user)],
) -> Success:
    """
    Invite the user with provided parent_email to become a parent of the student with provided student_email on course with provided course_id.

    Teacher OR Primary Instructor role required.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    parent_service = ParentService(db)
    personalization_service = PersonalizationService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        student = user_service.get_user(student_email)
        StudentPolicy.assert_student_access(student, course, db)
        parent = user_service.get_user(parent_email)
        TeacherPolicy.assert_not_teacher(parent, course, db)
        StudentPolicy.assert_not_student(parent, course, db)
        ParentPolicy.assert_not_parent_of_student(parent, student, course, db)
        if not ParentPolicy.check_parent_access(parent, course, db):
            personalization_service.add_course_participant(course, parent)
        parent_service.invite_parent(parent, student, course)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except student_errors.StudentRoleRequiredError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.RoleConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.delete("/students/{student_email}/parents/{parent_email}")
async def remove_parent(
    course_id: str,
    student_email: str,
    parent_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: Annotated[str, Depends(get_current_user)],
) -> Success:
    """
    Remove the parent identified by parent_email from the tracking of student with provided student_email on course with provided course_id.

    Teacher OR Primary Instructor OR Parent role required.

    Parent can only remove themselves.
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    parent_service = ParentService(db)
    personalization_service = PersonalizationService(db)
    try:
        teacher = user_service.get_user(teacher_email)
        course = course_service.get_course(course_id)
        if not teacher.isadmin:
            TeacherPolicy.assert_teacher_access(teacher, course, db)
        student = user_service.get_user(student_email)
        StudentPolicy.assert_student_access(student, course, db)
        parent = user_service.get_user(parent_email)
        ParentPolicy.assert_parent_of_student(parent, student, course, db)
        parent_service.remove_parent_student(parent, student, course)
        if not ParentPolicy.check_parent_access(parent, course, db):
            personalization_service.remove_course_participant(course, parent)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        parent_errors.ParentOfStudentRoleRequiredError,
        student_errors.StudentRoleRequiredError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.get("/parents/{parent_email}/students")
async def get_parents_children(
    course_id: str,
    parent_email: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: Annotated[str, Depends(get_current_user)],
) -> list[User]:
    """
    Get the list of students for the parent with provided email on course with provided course_id.

    Returns email and name for each child.

    - Teacher OR Primary Instructor can get the list of children for all parents
    - Parent can get the list of their children
    """
    user_service = UserService(db)
    course_service = CourseService(db)
    parent_service = ParentService(db)
    try:
        user = user_service.get_user(user_email)
        course = course_service.get_course(course_id)
        parent = user_service.get_user(parent_email)
        ParentPolicy.assert_access_to_parent(parent, user, course, db)
        students = parent_service.get_parents_children(parent, course)
        return [User.model_validate(st) for st in students]
    except user_errors.UserNotFoundError as e:
        if e.email == user_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (course_errors.CourseNotFoundError, parent_errors.ParentRoleRequiredError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.ParticipantRoleRequiredError,
        parent_errors.NoAccessToParentInfoError,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
