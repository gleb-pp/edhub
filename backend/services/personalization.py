from repo.courses import Course
from repo.users import User
from sqlalchemy.orm import Session
from repo.personalization import PersonalCourseInfo
from settings.course import course_settings
from random import randint
from sqlalchemy import func
import exceptions.courses as course_errors
import exceptions.personalization as personalization_errors
import logging


class PersonalizationService:
    """Service for managing personalization of courses for users."""

    logger = logging.getLogger(__name__)

    def __init__(self, db: Session):
        self.db = db

    def add_course_participant(self, course: Course, user: User) -> None:
        """Add the course personal info about the user when they enter the course."""
        self.logger.info(
            f"Adding course participant {user.email} to course {course.course_id}"
        )
        max_order = (
            self.db.query(func.max(PersonalCourseInfo.course_order))
            .filter(PersonalCourseInfo.email == user.email)
            .scalar()
        )
        new_order = (max_order or 0) + 1
        personal_info = PersonalCourseInfo(
            course_id=course.course_id,
            email=user.email,
            emoji_id=randint(0, course_settings.emoji_count - 1),
            course_order=new_order,
        )
        self.db.add(personal_info)

    def remove_course_participant(self, course: Course, user: User) -> None:
        """Remove the course personal info about the user when they leaves the course."""
        self.logger.info(
            f"Removing course participant {user.email} from course {course.course_id}"
        )
        personal_info = (
            self.db.query(PersonalCourseInfo)
            .filter(
                PersonalCourseInfo.course_id == course.course_id,
                PersonalCourseInfo.email == user.email,
            )
            .first()
        )
        if not personal_info:
            self.logger.warning(
                f"User {user.email} is not a participant in course {course.course_id}"
            )
            raise course_errors.ParticipantRoleRequired(user.email, course.course_id)
        self.db.delete(personal_info)

    def get_course_emoji(self, course: Course, user: User) -> int | None:
        """Get the personal course emoji for the provided user."""
        personal_info = (
            self.db.query(PersonalCourseInfo)
            .filter(
                PersonalCourseInfo.course_id == course.course_id,
                PersonalCourseInfo.email == user.email,
            )
            .first()
        )
        if not personal_info:
            self.logger.warning(
                f"User {user.email} is not a participant in course {course.course_id}"
            )
            raise course_errors.ParticipantRoleRequired(user.email, course.course_id)
        return personal_info.emoji_id

    def change_courses_order(self, user: User, new_order: list[str]) -> None:
        """Set the new section order within the provided course by the list of ordered section_ids."""
        self.logger.info(f"Changing courses order for user {user.email}")
        courses = [
            crs.course_id
            for crs in (
                self.db.query(PersonalCourseInfo)
                .filter(PersonalCourseInfo.email == user.email)
                .order_by(PersonalCourseInfo.course_order.asc())
                .all()
            )
        ]
        if len(courses) != len(new_order) or set(courses) != set(new_order):
            self.logger.warning(
                f"Incorrect courses order provided by user {user.email}"
            )
            raise personalization_errors.IncorrectCoursesOrderError

        for index, course_id in enumerate(new_order):
            self.db.query(PersonalCourseInfo).filter(
                PersonalCourseInfo.course_id == course_id,
                PersonalCourseInfo.email == user.email,
            ).update({"course_order": index})

    def set_course_emoji(
        self, course: Course, user: User, emoji_id: int | None
    ) -> None:
        """Set the personal course emoji for the provided user."""
        self.logger.info(
            f"Setting course emoji for user {user.email} in course {course.course_id} to {emoji_id}"
        )
        personal_info = (
            self.db.query(PersonalCourseInfo)
            .filter(
                PersonalCourseInfo.course_id == course.course_id,
                PersonalCourseInfo.email == user.email,
            )
            .first()
        )
        if not personal_info:
            self.logger.warning(
                f"User {user.email} is not a participant in course {course.course_id}"
            )
            raise course_errors.ParticipantRoleRequired(user.email, course.course_id)
        personal_info.emoji_id = emoji_id
