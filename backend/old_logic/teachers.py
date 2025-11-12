from fastapi import HTTPException
import constraints
import repo.teachers as repo_teachers
import logic.logging as logger


def get_course_teachers(db_cursor, course_id: str, user_email: str):
    # checking constraints
    constraints.assert_course_access(db_cursor, user_email, course_id)

    # finding assigned teachers
    teachers = repo_teachers.sql_select_course_teachers(db_cursor, course_id)

    res = [{"email": tch[0], "name": tch[1]} for tch in teachers]
    return res


def invite_teacher(db_conn, db_cursor, course_id: str, new_teacher_email: str, instructor_email: str):
    # checking constraints
    constraints.assert_instructor_access(db_cursor, instructor_email, course_id)
    constraints.assert_user_exists(db_cursor, new_teacher_email)

    # check if the teacher already assigned to course
    if constraints.check_teacher_access(db_cursor, new_teacher_email, course_id):
        raise HTTPException(
            status_code=409,
            detail="User to invite already has teacher right at this course",
        )

    # check if the potential teacher already has student rights at this course
    if constraints.check_student_access(db_cursor, new_teacher_email, course_id):
        raise HTTPException(status_code=409, detail="Can't invite course student as a teacher")

    # check if the potential teacher already has parent rights at this course
    if constraints.check_parent_access(db_cursor, new_teacher_email, course_id):
        raise HTTPException(status_code=409, detail="Can't invite parent as a teacher")

    # invite teacher
    repo_teachers.sql_insert_teacher(db_cursor, course_id, new_teacher_email)

    logger.log(db_conn, logger.TAG_TEACHER_ADD, f"Instructor {instructor_email} invited a teacher {new_teacher_email} to course {course_id}")

    return {"success": True}


def remove_teacher(db_conn, db_cursor, course_id: str, removing_teacher_email: str, user_email: str):
    # checking constraints
    if not (constraints.check_instructor_access(db_cursor, user_email, course_id) or
            (constraints.check_teacher_access(db_cursor, user_email, course_id) and removing_teacher_email == user_email)
    ):
        raise HTTPException(status_code=403, detail="User does not have permissions to delete this teacher")

    if constraints.check_instructor_access(db_cursor, removing_teacher_email, course_id):
        raise HTTPException(status_code=409, detail="Impossible to remove Primary Instructor")

    # check if the teacher assigned to the course
    if not constraints.check_teacher_access(db_cursor, removing_teacher_email, course_id):
        raise HTTPException(status_code=422, detail="User to remove is not a teacher at this course")

    # remove teacher
    repo_teachers.sql_delete_teacher(db_cursor, course_id, removing_teacher_email)

    logger.log(db_conn, logger.TAG_TEACHER_DEL, f"Teacher {user_email} removed a teacher {removing_teacher_email} from course {course_id}")

    return {"success": True}


def change_course_instructor(db_conn, db_cursor, course_id: str, teacher_email: str, instructor_email: str):
    # checking constraints
    constraints.assert_instructor_access(db_cursor, instructor_email, course_id)
    constraints.assert_teacher_access(db_cursor, teacher_email, course_id)

    repo_teachers.sql_update_instructor(db_cursor, course_id, instructor_email, teacher_email)

    logger.log(db_conn, logger.TAG_INSTRUCTOR_EDIT, f"Course {course_id} now have new instructor {teacher_email} instead of {instructor_email}")

    return {"success": True}
