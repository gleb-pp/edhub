import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.parents import (
    get_students_parents,
    invite_parent,
    remove_parent,
    get_parents_children
)
from src.exceptions import courses as course_errors
from src.exceptions import parents as parent_errors
from src.exceptions import students as student_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success


pytestmark = pytest.mark.asyncio


class TestParentsRouter:

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.ParentService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_get_students_parents_success_as_teacher(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_parent_service_class,
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
        mock_parent_service = MagicMock()
        mock_parent_service_class.return_value = mock_parent_service

        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_student = MagicMock()
        mock_parents = [MagicMock(), MagicMock()]

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_parent_service.get_students_parents.return_value = mock_parents

        with (
            patch('src.routers.parents.StudentPolicy.assert_access_to_student') as mock_assert_access,
            patch('src.routers.parents.User.model_validate') as mock_validate
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_students_parents(
                "course-123", "student@test.com", mock_db, "teacher@test.com"
            )

        assert len(result) == 2
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_student, mock_user, mock_course, mock_db)
        mock_parent_service.get_students_parents.assert_called_once_with(mock_student, mock_course)
        assert mock_validate.call_count == 2

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_get_students_parents_user_not_found(
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
            await get_students_parents("course-123", "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_get_students_parents_course_not_found(
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
        mock_student = MagicMock()

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await get_students_parents("course-123", "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_get_students_parents_student_role_required(
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
        mock_student = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.parents.StudentPolicy.assert_access_to_student') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = student_errors.NoAccessToStudentInfoError(
                "student@test.com", "user@test.com", "course-123"
            )
            await get_students_parents("course-123", "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.ParentService')
    @patch('src.routers.parents.PersonalizationService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_invite_parent_success_as_teacher(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_parent_service_class,
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
        mock_parent_service = MagicMock()
        mock_parent_service_class.return_value = mock_parent_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_student = MagicMock()
        mock_parent = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.parents.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            patch('src.routers.parents.StudentPolicy.assert_student_access') as mock_assert_student,
            patch('src.routers.parents.TeacherPolicy.assert_not_teacher') as mock_assert_not_teacher,
            patch('src.routers.parents.StudentPolicy.assert_not_student') as mock_assert_not_student,
            patch('src.routers.parents.ParentPolicy.assert_not_parent_of_student') as mock_assert_not_parent,
            patch('src.routers.parents.ParentPolicy.check_parent_access', return_value=False)
        ):
            result = await invite_parent(
                "course-123", "student@test.com", "parent@test.com", mock_db, "teacher@test.com"
            )

        assert result.success is True
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call("student@test.com")
        mock_user_service.get_user.assert_any_call("parent@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assert_not_teacher.assert_called_once_with(mock_parent, mock_course, mock_db)
        mock_assert_not_student.assert_called_once_with(mock_parent, mock_course, mock_db)
        mock_assert_not_parent.assert_called_once_with(mock_parent, mock_student, mock_course, mock_db)
        mock_personalization_service.add_course_participant.assert_called_once_with(mock_course, mock_parent)
        mock_parent_service.invite_parent.assert_called_once_with(mock_parent, mock_student, mock_course)
        mock_db.commit.assert_called_once()

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.ParentService')
    @patch('src.routers.parents.PersonalizationService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_invite_parent_parent_already_in_course(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_parent_service_class,
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
        mock_parent_service = MagicMock()
        mock_parent_service_class.return_value = mock_parent_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_student = MagicMock()
        mock_parent = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.parents.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.parents.StudentPolicy.assert_student_access'),
            patch('src.routers.parents.TeacherPolicy.assert_not_teacher'),
            patch('src.routers.parents.StudentPolicy.assert_not_student'),
            patch('src.routers.parents.ParentPolicy.assert_not_parent_of_student'),
            patch('src.routers.parents.ParentPolicy.check_parent_access', return_value=True)
        ):
            result = await invite_parent(
                "course-123", "student@test.com", "parent@test.com", mock_db, "teacher@test.com"
            )

        assert result.success is True
        mock_personalization_service.add_course_participant.assert_not_called()
        mock_parent_service.invite_parent.assert_called_once()

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_invite_parent_teacher_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("teacher@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await invite_parent(
                "course-123", "student@test.com", "parent@test.com", mock_db, "teacher@test.com"
            )

        assert exc_info.value.status_code == 401

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_invite_parent_student_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
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

        mock_teacher = MagicMock()
        mock_user_service.get_user.side_effect = [mock_teacher, user_errors.UserNotFoundError("student@test.com")]

        with pytest.raises(HTTPException) as exc_info:
            await invite_parent(
                "course-123", "student@test.com", "parent@test.com", mock_db, "teacher@test.com"
            )

        assert exc_info.value.status_code == 400

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_invite_parent_teacher_role_required(
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

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.parents.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123")
            await invite_parent(
                "course-123", "student@test.com", "parent@test.com", mock_db, "student@test.com"
            )

        assert exc_info.value.status_code == 403

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_invite_parent_conflict(
        self,
        mock_get_current_user,
        mock_get_db,
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

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_student = MagicMock()
        mock_parent = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.parents.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.parents.StudentPolicy.assert_student_access'),
            patch('src.routers.parents.TeacherPolicy.assert_not_teacher') as mock_assert_not_teacher,
            patch('src.routers.parents.ParentPolicy.assert_not_parent_of_student'),
            patch('src.routers.parents.ParentPolicy.check_parent_access', return_value=False),
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_not_teacher.side_effect = teacher_errors.TeacherRoleConflictError("parent@test.com", "course-123")
            await invite_parent(
                "course-123", "student@test.com", "parent@test.com", mock_db, "teacher@test.com"
            )

        assert exc_info.value.status_code == 409

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.ParentService')
    @patch('src.routers.parents.PersonalizationService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_remove_parent_success_as_teacher(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_parent_service_class,
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
        mock_parent_service = MagicMock()
        mock_parent_service_class.return_value = mock_parent_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_student = MagicMock()
        mock_parent = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.parents.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            patch('src.routers.parents.StudentPolicy.assert_student_access') as mock_assert_student,
            patch('src.routers.parents.ParentPolicy.assert_parent_of_student') as mock_assert_parent,
            patch('src.routers.parents.ParentPolicy.check_parent_access', return_value=False)
        ):
            result = await remove_parent(
                "course-123", "student@test.com", "parent@test.com", mock_db, "teacher@test.com"
            )

        assert result.success is True
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assert_parent.assert_called_once_with(mock_parent, mock_student, mock_course, mock_db)
        mock_parent_service.remove_parent_student.assert_called_once_with(mock_parent, mock_student, mock_course)
        mock_personalization_service.remove_course_participant.assert_called_once_with(mock_course, mock_parent)
        mock_db.commit.assert_called_once()

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.ParentService')
    @patch('src.routers.parents.PersonalizationService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_remove_parent_parent_still_in_course(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_personalization_service_class,
        mock_parent_service_class,
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
        mock_parent_service = MagicMock()
        mock_parent_service_class.return_value = mock_parent_service
        mock_personalization_service = MagicMock()
        mock_personalization_service_class.return_value = mock_personalization_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_student = MagicMock()
        mock_parent = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.parents.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.parents.StudentPolicy.assert_student_access'),
            patch('src.routers.parents.ParentPolicy.assert_parent_of_student'),
            patch('src.routers.parents.ParentPolicy.check_parent_access', return_value=True)
        ):
            result = await remove_parent(
                "course-123", "student@test.com", "parent@test.com", mock_db, "teacher@test.com"
            )

        assert result.success is True
        mock_personalization_service.remove_course_participant.assert_not_called()

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_remove_parent_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
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

        mock_teacher = MagicMock()
        mock_student = MagicMock()
        mock_parent = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.parents.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.parents.StudentPolicy.assert_student_access'),
            patch('src.routers.parents.ParentPolicy.assert_parent_of_student') as mock_assert_parent,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_parent.side_effect = parent_errors.ParentOfStudentRoleRequiredError(
                "parent@test.com", "student@test.com", "course-123"
            )
            await remove_parent(
                "course-123", "student@test.com", "parent@test.com", mock_db, "teacher@test.com"
            )

        assert exc_info.value.status_code == 400

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.ParentService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_get_parents_children_success_as_teacher(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_parent_service_class,
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
        mock_parent_service = MagicMock()
        mock_parent_service_class.return_value = mock_parent_service

        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_parent = MagicMock()
        mock_children = [MagicMock(), MagicMock()]

        mock_user_service.get_user.side_effect = [mock_user, mock_parent]
        mock_course_service.get_course.return_value = mock_course
        mock_parent_service.get_parents_children.return_value = mock_children

        with (
            patch('src.routers.parents.ParentPolicy.assert_access_to_parent') as mock_assert_access,
            patch('src.routers.parents.User.model_validate') as mock_validate
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_parents_children(
                "course-123", "parent@test.com", mock_db, "teacher@test.com"
            )

        assert len(result) == 2
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call("parent@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_parent, mock_user, mock_course, mock_db)
        mock_parent_service.get_parents_children.assert_called_once_with(mock_parent, mock_course)
        assert mock_validate.call_count == 2

    @patch('src.routers.parents.UserService')
    @patch('src.routers.parents.CourseService')
    @patch('src.routers.parents.get_db')
    @patch('src.routers.parents.get_current_user')
    async def test_get_parents_children_access_denied(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "stranger@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service

        mock_user = MagicMock()
        mock_parent = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_user, mock_parent]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.parents.ParentPolicy.assert_access_to_parent') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = parent_errors.NoAccessToParentInfoError(
                "parent@test.com", "stranger@test.com", "course-123"
            )
            await get_parents_children(
                "course-123", "parent@test.com", mock_db, "stranger@test.com"
            )

        assert exc_info.value.status_code == 403
