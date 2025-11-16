from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from models.common import Success
from models.users import User
from typing import Annotated
from sqlalchemy.orm import Session
from db import get_db
import logic.users as user_logic
import exceptions.users as user_errors
import logic.courses as course_logic
import exceptions.courses as course_errors
import logic.teachers as teacher_logic
import exceptions.teachers as teacher_errors
import logic.students as student_logic
import logic.parents as parent_logic
import logic.personalization as personalization_logic


router = APIRouter(
    prefix='/{course_id}/teachers',
    tags=["Teachers"],
)



@router.get("/")
async def get_course_teachers(
    course_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_email: str = Depends(get_current_user)
) -> list[User]:
    """
    Get the list of teachers teaching the course with the provided course_id.

    Does NOT return the Primary Instructor.

    Course role (Primary Instructor, Teacher, Student, Parent) required.
    """
    try:
        user = user_logic.get_user(user_email, db)
        course = course_logic.get_course(course_id, db)
        course_logic.assert_course_access(user, course, db)
        teachers = teacher_logic.get_course_teachers(course, db)
        return [User.model_validate(tchr) for tchr in teachers]
    except user_errors.UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except course_errors.ParticipantRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/")
async def invite_teacher(
    course_id: str,
    new_teacher_email: str,
    db: Annotated[Session, Depends(get_db)],
    teacher_email: str = Depends(get_current_user),
) -> Success:
    """
    Add the user with provided new_teacher_email as a teacher to the course with provided course_id.

    Primary Instructor role required.
    """
    try:
        teacher = user_logic.get_user(teacher_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_instructor_access(teacher, course, db)
        new_teacher = user_logic.get_user(new_teacher_email, db)
        teacher_logic.assert_not_teacher(new_teacher, course, db)
        student_logic.assert_not_student(new_teacher, course, db)
        parent_logic.assert_not_parent(new_teacher, course, db)
        teacher_logic.invite_teacher(new_teacher, course, db)
        personalization_logic.add_course_participant(course, new_teacher, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == teacher_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        elif e.email == new_teacher_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.InstructorRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except course_errors.RoleConflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.delete("/{removing_teacher_email}")
async def remove_teacher(
    course_id: str,
    teacher_email: str,
    db: Annotated[Session, Depends(get_db)],
    instructor_email: str = Depends(get_current_user),
) -> Success:
    """
    Remove the teacher with removing_teacher_email from the course with provided course_id.

    Primary Instructor role required.

    Primary Instructor can't remove themself until they are Primary Instructor.
    """
    try:
        instructor = user_logic.get_user(instructor_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_instructor_access(instructor, course, db)
        teacher = user_logic.get_user(teacher_email, db)
        teacher_logic.assert_teacher_access(teacher, course, db)
        teacher_logic.remove_teacher(teacher, course, db)
        personalization_logic.remove_course_participant(course, teacher, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == instructor_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        elif e.email == teacher_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.InstructorRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.patch("/change_course_instructor", tags=["Courses"])
async def change_course_instructor(
    course_id: str,
    teacher_email: str,
    db: Annotated[Session, Depends(get_db)],
    instructor_email: str = Depends(get_current_user)
) -> Success:
    """
    Transfer the course ownership (Primary Instructor role) to other Teacher within the course.

    Primary Instructor role required.
    """
    try:
        instructor = user_logic.get_user(instructor_email, db)
        course = course_logic.get_course(course_id, db)
        teacher_logic.assert_instructor_access(instructor, course, db)
        teacher = user_logic.get_user(teacher_email, db)
        teacher_logic.assert_teacher_access(teacher, course, db)
        teacher_logic.change_course_instructor(instructor, teacher, course, db)
        db.commit()
        return Success(success=True)
    except user_errors.UserNotFoundError as e:
        if e.email == instructor_email:
            raise HTTPException(status_code=401, detail=str(e)) from e
        elif e.email == teacher_email:
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except course_errors.CourseNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except teacher_errors.InstructorRoleRequired as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except teacher_errors.TeacherRoleRequired as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
