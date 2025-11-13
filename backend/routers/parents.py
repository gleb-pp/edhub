from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
import logic.parents
from models.common import Success
from models.users import User
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
import logic.parents as parent_logic
import logic.users as user_logic
import logic.students as student_logic
import exceptions.courses as course_errors
import logic.courses as course_logic
import logic.teachers as teacher_logic
import exceptions.users as user_errors
import exceptions.teachers as teacher_errors
import exceptions.students as student_errors
import exceptions.parents as parent_errors


router = APIRouter(
    tags=["Parents"],
)


@router.get("{course_id}/parents/{student_email}")
async def get_students_parents(
    course_id: str,
    student_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user)
) -> list[User]:
    """
    Get the list of parents observing the student with provided email on course with provided course_id.

    Teacher OR Primary Instructor role required.
    """
    try:
        teacher = user_logic.get_user(teacher_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_teacher_access(teacher, course, db)
        student = user_logic.get_user(student_email, db)
        student_logic.assert_student_access(student, course, db)
        parents = parent_logic.get_students_parents(student, course, db)
        return [User.model_validate(par) for par in parents]
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        elif e.email == student_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except student_errors.StudentRoleRequired as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# TODO: get_my_parents

@router.post("{course_id}/parents/{student_email}")
async def invite_parent(
    course_id: str,
    student_email: str,
    parent_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Invite the user with provided parent_email to become a parent of the student with provided student_email on course with provided course_id.

    Teacher OR Primary Instructor role required.
    """
    try:
        teacher = user_logic.get_user(teacher_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_teacher_access(teacher, course, db)
        student = user_logic.get_user(student_email, db)
        student_logic.assert_student_access(student, course, db)
        parent = user_logic.get_user(parent_email, db)
        teacher_logic.assert_not_teacher(parent, course, db)
        student_logic.assert_not_student(parent, course, db)
        parent_logic.assert_not_parent_of_student(parent, student, course, db)
        parent_logic.invite_parent(parent, student, course, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except student_errors.StudentRoleRequired as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.RoleConflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.delete("{course_id}/parents/{student_email}/{parent_email}")
async def remove_parent(
    course_id: str,
    student_email: str,
    parent_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Remove the parent identified by parent_email from the tracking of student with provided student_email on course with provided course_id.

    Teacher OR Primary Instructor OR Parent role required.

    Parent can only remove themselves.
    """
    try:
        teacher = user_logic.get_user(teacher_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_teacher_access(teacher, course, db)
        student = user_logic.get_user(student_email, db)
        student_logic.assert_student_access(student, course, db)
        parent = user_logic.get_user(parent_email, db)
        parent_logic.assert_parent_of_student(parent, student, course, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        parent_errors.ParentOfStudentRoleRequired
     ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except parent_errors.ParentOfStudentRoleRequired as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.get("{course_id}/children/{parent_email}")
async def get_parents_children(
    course_id: str,
    parent_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user)
) -> list[User]:
    """
    Get the list of students for the parent with provided email on course with provided course_id.

    Returns email and name for each child.

    Teacher OR Primary Instructor role required.
    """
    try:
        teacher = user_logic.get_user(teacher_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_teacher_access(teacher, course, db)
        parent = user_logic.get_user(parent_email, db)
        parent_logic.assert_parent_access(parent, course, db)
        students = parent_logic.get_parents_children(parent, course, db)
        return [User.model_validate(st) for st in students]
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except parent_errors.ParentRoleRequired as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# TODO: get_my_children
