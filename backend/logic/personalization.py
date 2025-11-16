from repo.courses import Course
from repo.users import User
from sqlalchemy.orm import Session
from repo.personalization import PersonalCourseInfo
from settings.course import course_settings
from random import randint
from sqlalchemy import func
import exceptions.courses as course_errors
import logic.courses as course_logic
import exceptions.personalization as personalization_errors

def add_course_participant(course: Course, user: User, db: Session) -> None:
    """Add the course personal info about the user when they enter the course."""
    max_order = db.query(func.max(PersonalCourseInfo.course_order)) \
                  .filter(PersonalCourseInfo.email == user.email) \
                  .scalar()
    new_order = (max_order or 0) + 1
    personal_info = PersonalCourseInfo(
        course_id=course.course_id, 
        email=user.email,
        emoji_id=randint(0, course_settings.emoji_count - 1),
        course_order=new_order
    )
    db.add(personal_info)


def remove_course_participant(course: Course, user: User, db: Session) -> None:
    """Remove the course personal info about the user when they leaves the course."""
    personal_info = db.query(PersonalCourseInfo).filter(PersonalCourseInfo.course_id == course.course_id, PersonalCourseInfo.email==user.email).first()
    if not personal_info:
        raise course_errors.ParticipantRoleRequired(user.email, course.course_id)
    db.delete(personal_info)


def get_course_emoji(course: Course, user: User, db: Session) -> int | None:
    """Get the personal course emoji for the provided user."""
    personal_info = db.query(PersonalCourseInfo).filter(PersonalCourseInfo.course_id == course.course_id, PersonalCourseInfo.email==user.email).first()
    if not personal_info:
        raise course_errors.ParticipantRoleRequired(user.email, course.course_id)
    return personal_info.emoji_id


def change_courses_order(user: User, new_order: list[str], db: Session) -> None:
    """Set the new section order within the provided course by the list of ordered section_ids."""
    courses = [crs.course_id for crs in course_logic.get_available_courses(user, db)]
    if len(courses) != new_order or set(courses) != set(new_order):
        raise personalization_errors.IncorrectCoursesOrderError
    
    for index, course_id in enumerate(new_order):
        db.query(PersonalCourseInfo).filter(
            PersonalCourseInfo.course_id == course_id,
            PersonalCourseInfo.email == user.email
        ).update({"course_order": index})


def set_course_emoji(course: Course, user: User, emoji_id: int | None, db: Session) -> None:
    personal_info = db.query(PersonalCourseInfo).filter(PersonalCourseInfo.course_id == course.course_id, PersonalCourseInfo.email==user.email).first()
    if not personal_info:
        raise course_errors.ParticipantRoleRequired(user.email, course.course_id)
    personal_info.emoji_id = emoji_id
