from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from models.common import Success
from models.users import User
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
import services.parents as parent_logic
import services.users as user_logic
import services.students as student_logic
import exceptions.courses as course_errors
import services.courses as course_logic
import services.teachers as teacher_logic
import exceptions.users as user_errors
import exceptions.teachers as teacher_errors
import exceptions.students as student_errors
import exceptions.parents as parent_errors
import services.personalization as personalization_logic


router = APIRouter(
    tags=["Parents"],
)


@router.get("{course_id}/parents/{student_email}")
async def get_students_parents(
    course_id: str,
    student_email: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user)
) -> list[User]:
    """
    Get the list of parents observing the student with provided email on course with provided course_id.

    - Teacher OR Primary Instructor can get the list of parents for all students
    - Parent can get the list of parents for their children
    - Student can get the list of their parents
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        student = user_logic.get_user(student_email, db)
        student_logic.assert_access_to_student(student, user, course, db)
        parents = parent_logic.get_students_parents(student, course, db)
        return [User.model_validate(par) for par in parents]
    except user_errors.UserNotFoundError as e:
        if e.email == user_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        student_errors.StudentRoleRequired
     ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.ParticipantRoleRequired,
        student_errors.NoAccessToStudentInfo,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


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
        if not teacher.isadmin:
            teacher_logic.assert_teacher_access(teacher, course, db)
        student = user_logic.get_user(student_email, db)
        student_logic.assert_student_access(student, course, db)
        parent = user_logic.get_user(parent_email, db)
        teacher_logic.assert_not_teacher(parent, course, db)
        student_logic.assert_not_student(parent, course, db)
        parent_logic.assert_not_parent_of_student(parent, student, course, db)
        if not parent_logic.check_parent_access(parent, course, db):
            personalization_logic.add_course_participant(course, parent, db)
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
        if not teacher.isadmin:
            teacher_logic.assert_teacher_access(teacher, course, db)
        student = user_logic.get_user(student_email, db)
        student_logic.assert_student_access(student, course, db)
        parent = user_logic.get_user(parent_email, db)
        parent_logic.assert_parent_of_student(parent, student, course, db)
        parent_logic.remove_parent_student(parent, student, course, db)
        if not parent_logic.check_parent_access(parent, course, db):
            personalization_logic.remove_course_participant(course, parent, db)
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


@router.get("{course_id}/children/{parent_email}")
async def get_parents_children(
    course_id: str,
    parent_email: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user)
) -> list[User]:
    """
    Get the list of students for the parent with provided email on course with provided course_id.

    Returns email and name for each child.

    - Teacher OR Primary Instructor can get the list of children for all parents
    - Parent can get the list of their children
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        parent = user_logic.get_user(parent_email, db)
        parent_logic.assert_access_to_parent(parent, user, course, db)
        students = parent_logic.get_parents_children(parent, course, db)
        return [User.model_validate(st) for st in students]
    except user_errors.UserNotFoundError as e:
        if e.email == user_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.CourseNotFoundError,
        parent_errors.ParentRoleRequired
     ) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except (
        course_errors.ParticipantRoleRequired,
        parent_errors.NoAccessToParentInfo,
    ) as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
