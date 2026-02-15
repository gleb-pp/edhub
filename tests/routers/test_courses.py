import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.courses import (
    get_available_courses,
    create_course,
    delete_course,
    get_course_info,
    leave_course
)
from src.exceptions import courses as course_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success


pytestmark = pytest.mark.asyncio


class TestCoursesRouter:

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_get_available_courses_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_courses = [MagicMock(), MagicMock()]
        for i, course in enumerate(mock_courses):
            course.course_id = f"course-{i+1}"
            course.title = f"Course {i+1}"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_available_courses.return_value = mock_courses

        with patch('src.routers.courses.Course.model_validate') as mock_validate:
            mock_validate.side_effect = lambda x: {"course_id": x.course_id, "title": x.title}
            result = await get_available_courses(mock_db, "user@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.get_available_courses.assert_called_once_with(mock_user)
        assert mock_validate.call_count == 2

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_get_available_courses_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_available_courses(mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.PersonalizationService')
    @patch('src.routers.courses.SectionService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_create_course_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_personalization_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_course.course_id = "new-course-123"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.create_course.return_value = mock_course

        with patch('src.routers.courses.CourseID.model_validate') as mock_validate:
            expected_result = {"course_id": "new-course-123"}
            mock_validate.return_value = expected_result
            result = await create_course(mock_db, "user@test.com", "Test Course", "Test Org")

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("user@test.com")
        mock_course_service.create_course.assert_called_once_with("Test Course", "Test Org", mock_user)
        mock_personalization_service.add_course_participant.assert_called_once_with(mock_course, mock_user)
        mock_section_service.create_section.assert_called_once_with("General", mock_course)
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_course)

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.PersonalizationService')
    @patch('src.routers.courses.SectionService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_create_course_without_organization(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_personalization_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_course.course_id = "new-course-123"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.create_course.return_value = mock_course

        with patch('src.routers.courses.CourseID.model_validate') as mock_validate:
            expected_result = {"course_id": "new-course-123"}
            mock_validate.return_value = expected_result
            result = await create_course(mock_db, "user@test.com", "Test Course", None)

        assert result == expected_result
        mock_course_service.create_course.assert_called_once_with("Test Course", None, mock_user)

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_create_course_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await create_course(mock_db, "user@test.com", "Test Course", "Test Org")

        assert exc_info.value.status_code == 401

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_delete_course_success_as_instructor(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()
        mock_course.course_id = "course-123"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.courses.TeacherPolicy.assert_instructor_access') as mock_assert_instructor:
            result = await delete_course("course-123", mock_db, "instructor@test.com")

        assert isinstance(result, Success)
        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("instructor@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_instructor.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_course_service.delete_course.assert_called_once_with(mock_course)
        mock_db.commit.assert_called_once()

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_delete_course_success_as_admin(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user.isadmin = True
        mock_course = MagicMock()
        mock_course.course_id = "course-123"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        result = await delete_course("course-123", mock_db, "admin@test.com")

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("admin@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_course_service.delete_course.assert_called_once_with(mock_course)
        mock_db.commit.assert_called_once()

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_delete_course_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await delete_course("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_delete_course_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user.isadmin = False

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await delete_course("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_delete_course_instructor_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.courses.TeacherPolicy.assert_instructor_access') as mock_assert_instructor:
            mock_assert_instructor.side_effect = teacher_errors.InstructorRoleRequiredError("student@test.com", "course-123")

            with pytest.raises(HTTPException) as exc_info:
                await delete_course("course-123", mock_db, "student@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_get_course_info_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()
        mock_course.course_id = "course-123"
        mock_course.title = "Test Course"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.courses.CoursePolicy.assert_course_access') as mock_assert_access:
            with patch('src.routers.courses.Course.model_validate') as mock_validate:
                expected_result = {"course_id": "course-123", "title": "Test Course"}
                mock_validate.return_value = expected_result
                result = await get_course_info("course-123", mock_db, "student@test.com")

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_validate.assert_called_once_with(mock_course)

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_get_course_info_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_course_info("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_get_course_info_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await get_course_info("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_get_course_info_participant_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "non-participant@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.courses.CoursePolicy.assert_course_access') as mock_assert_access:
            mock_assert_access.side_effect = course_errors.ParticipantRoleRequiredError("non-participant@test.com", "course-123")

            with pytest.raises(HTTPException) as exc_info:
                await get_course_info("course-123", mock_db, "non-participant@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.StudentService')
    @patch('src.routers.courses.TeacherService')
    @patch('src.routers.courses.ParentService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_leave_course_as_student(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_parent_service_class,
        mock_teacher_service_class,
        mock_student_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_student_service = MagicMock()
        mock_student_service_class.return_value = mock_student_service
        mock_teacher_service = MagicMock()
        mock_teacher_service_class.return_value = mock_teacher_service
        mock_parent_service = MagicMock()
        mock_parent_service_class.return_value = mock_parent_service

        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_course.course_id = "course-123"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with patch('src.routers.courses.StudentPolicy.check_student_access', return_value=True):
            with patch('src.routers.courses.TeacherPolicy.check_teacher_access', return_value=False):
                with patch('src.routers.courses.ParentPolicy.check_parent_access', return_value=False):
                    with patch('src.routers.courses.TeacherPolicy.check_instructor_access', return_value=False):
                        result = await leave_course("course-123", mock_db, "student@test.com")

        assert result.success is True
        mock_student_service.remove_student.assert_called_once_with(mock_user, mock_course)
        mock_db.commit.assert_called_once()

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.StudentService')
    @patch('src.routers.courses.TeacherService')
    @patch('src.routers.courses.ParentService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_leave_course_as_teacher(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_parent_service_class,
        mock_teacher_service_class,
        mock_student_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_student_service = MagicMock()
        mock_student_service_class.return_value = mock_student_service
        mock_teacher_service = MagicMock()
        mock_teacher_service_class.return_value = mock_teacher_service
        mock_parent_service = MagicMock()
        mock_parent_service_class.return_value = mock_parent_service

        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_course.course_id = "course-123"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.courses.StudentPolicy.check_student_access', return_value=False),
            patch('src.routers.courses.TeacherPolicy.check_teacher_access', return_value=True),
            patch('src.routers.courses.ParentPolicy.check_parent_access', return_value=False),
            patch('src.routers.courses.TeacherPolicy.check_instructor_access', return_value=False)
        ):
            result = await leave_course("course-123", mock_db, "teacher@test.com")

        assert result.success is True
        mock_teacher_service.remove_teacher.assert_called_once_with(mock_user, mock_course)
        mock_db.commit.assert_called_once()

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.StudentService')
    @patch('src.routers.courses.TeacherService')
    @patch('src.routers.courses.ParentService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_leave_course_as_parent(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_parent_service_class,
        mock_teacher_service_class,
        mock_student_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "parent@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_student_service = MagicMock()
        mock_student_service_class.return_value = mock_student_service
        mock_teacher_service = MagicMock()
        mock_teacher_service_class.return_value = mock_teacher_service
        mock_parent_service = MagicMock()
        mock_parent_service_class.return_value = mock_parent_service

        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_course.course_id = "course-123"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.courses.StudentPolicy.check_student_access', return_value=False),
            patch('src.routers.courses.TeacherPolicy.check_teacher_access', return_value=False),
            patch('src.routers.courses.ParentPolicy.check_parent_access', return_value=True),
            patch('src.routers.courses.TeacherPolicy.check_instructor_access', return_value=False)
        ):
            result = await leave_course("course-123", mock_db, "parent@test.com")

        assert result.success is True
        mock_parent_service.remove_parent.assert_called_once_with(mock_user, mock_course)
        mock_db.commit.assert_called_once()

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_leave_course_as_instructor(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "instructor@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_course.course_id = "course-123"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.courses.StudentPolicy.check_student_access', return_value=False),
            patch('src.routers.courses.TeacherPolicy.check_teacher_access', return_value=False),
            patch('src.routers.courses.ParentPolicy.check_parent_access', return_value=False),
            patch('src.routers.courses.TeacherPolicy.check_instructor_access', return_value=True),
            pytest.raises(HTTPException) as exc_info
        ):
            await leave_course("course-123", mock_db, "instructor@test.com")

        assert exc_info.value.status_code == 403
        assert "primary instructor" in str(exc_info.value.detail).lower()

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_leave_course_no_role(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "non-participant@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_course.course_id = "course-123"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.courses.StudentPolicy.check_student_access', return_value=False),
            patch('src.routers.courses.TeacherPolicy.check_teacher_access', return_value=False),
            patch('src.routers.courses.ParentPolicy.check_parent_access', return_value=False),
            patch('src.routers.courses.TeacherPolicy.check_instructor_access', return_value=False),
            pytest.raises(HTTPException) as exc_info
        ):
            await leave_course("course-123", mock_db, "non-participant@test.com")

        assert exc_info.value.status_code == 403
        assert "not a participant" in str(exc_info.value.detail).lower()

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_leave_course_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await leave_course("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.courses.UserService')
    @patch('src.routers.courses.CourseService')
    @patch('src.routers.courses.get_db')
    @patch('src.routers.courses.get_current_user')
    async def test_leave_course_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await leave_course("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400
