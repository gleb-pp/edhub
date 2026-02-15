from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import assignments as assignment_errors
from src.exceptions import courses as course_errors
from src.exceptions import sections as section_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.routers.assignments import (
    create_assignment,
    get_assignment,
    get_course_assignments,
    remove_assignment,
)

pytestmark = pytest.mark.asyncio


class TestAssignmentsRouter:

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.SectionService")
    @patch("src.routers.assignments.AssignmentService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_create_assignment_success_as_teacher(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_course.course_id = "course-123"
        mock_section = MagicMock()
        mock_section.section_id = 1
        mock_assignment = MagicMock()
        mock_assignment.course_id = "course-123"
        mock_assignment.assignment_id = 42
        mock_assignment.section_id = 1

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.return_value = mock_section
        mock_assignment_service.create_assignment.return_value = mock_assignment

        with (
            patch("src.routers.assignments.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.assignments.AssignmentID.model_validate") as mock_validate
        ):
            expected_result = {"course_id": "course-123", "assignment_id": 42, "section_id": 1}
            mock_validate.return_value = expected_result
            result = await create_assignment(
                "course-123", 1, mock_db, "Test Title", "Test Description", "teacher@test.com",
            )

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_section_service.get_section.assert_called_once_with(mock_course, 1)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assignment_service.create_assignment.assert_called_once_with(
            mock_section, "Test Title", "Test Description", mock_teacher,
        )
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_assignment)

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.SectionService")
    @patch("src.routers.assignments.AssignmentService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_create_assignment_success_as_admin(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "admin@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = True
        mock_course = MagicMock()
        mock_course.course_id = "course-123"
        mock_section = MagicMock()
        mock_section.section_id = 1
        mock_assignment = MagicMock()
        mock_assignment.course_id = "course-123"
        mock_assignment.assignment_id = 42
        mock_assignment.section_id = 1

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.return_value = mock_section
        mock_assignment_service.create_assignment.return_value = mock_assignment

        with patch("src.routers.assignments.AssignmentID.model_validate") as mock_validate:
            expected_result = {"course_id": "course-123", "assignment_id": 42, "section_id": 1}
            mock_validate.return_value = expected_result
            result = await create_assignment(
                "course-123", 1, mock_db, "Test Title", "Test Description", "admin@test.com",
            )

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("admin@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_section_service.get_section.assert_called_once_with(mock_course, 1)
        mock_assignment_service.create_assignment.assert_called_once_with(
            mock_section, "Test Title", "Test Description", mock_teacher,
        )
        mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(mock_assignment)

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_create_assignment_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("teacher@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await create_assignment(
                "course-123", 1, mock_db, "Test Title", "Test Description", "teacher@test.com",
            )

        assert exc_info.value.status_code == 401

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_create_assignment_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class,
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

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await create_assignment(
                "course-123", 1, mock_db, "Test Title", "Test Description", "teacher@test.com",
            )

        assert exc_info.value.status_code == 400

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.SectionService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_create_assignment_section_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_section_service.get_section.side_effect = section_errors.SectionNotFoundError(1, "course-123")

        with pytest.raises(HTTPException) as exc_info:
            await create_assignment(
                "course-123", 1, mock_db, "Test Title", "Test Description", "teacher@test.com",
            )

        assert exc_info.value.status_code == 400

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.SectionService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_create_assignment_teacher_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_section_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_section_service = MagicMock()
        mock_section_service_class.return_value = mock_section_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.assignments.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123")
            await create_assignment(
                "course-123", 1, mock_db, "Test Title", "Test Description", "student@test.com",
            )

        assert exc_info.value.status_code == 403

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.AssignmentService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_remove_assignment_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_course.course_id = "course-123"
        mock_assignment = MagicMock()
        mock_assignment.assignment_id = 10

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment

        with patch("src.routers.assignments.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
            result = await remove_assignment("course-123", 10, mock_db, "teacher@test.com")

        assert isinstance(result, Success)
        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, 10)
        mock_assignment_service.delete_assignment.assert_called_once_with(mock_assignment)
        mock_db.commit.assert_called_once()

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.AssignmentService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_remove_assignment_assignment_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.side_effect = assignment_errors.AssignmentNotFoundError("course-123", 999)

        with pytest.raises(HTTPException) as exc_info:
            await remove_assignment("course-123", 999, mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 400

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_remove_assignment_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class,
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

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await remove_assignment("course-123", 10, mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 400

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.AssignmentService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_assignment_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_assignment.course_id = "course-123"
        mock_assignment.assignment_id = 10
        mock_assignment.section_id = 1
        mock_assignment.title = "Test Assignment"
        mock_assignment.description = "Test Description"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment

        with (
            patch("src.routers.assignments.CoursePolicy.assert_course_access") as mock_assert_access,
            patch("src.routers.assignments.Assignment.model_validate") as mock_validate
        ):
            expected_result = {"course_id": "course-123", "assignment_id": 10, "title": "Test Assignment"}
            mock_validate.return_value = expected_result
            result = await get_assignment("course-123", 10, mock_db, "student@test.com")

        assert result == expected_result
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, 10)
        mock_validate.assert_called_once_with(mock_assignment)

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_assignment_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_assignment("course-123", 10, mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_assignment_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class,
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
            await get_assignment("course-123", 10, mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.AssignmentService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_assignment_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.side_effect = assignment_errors.AssignmentNotFoundError("course-123", 999)

        with pytest.raises(HTTPException) as exc_info:
            await get_assignment("course-123", 999, mock_db, "user@test.com")

        assert exc_info.value.status_code == 404

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.AssignmentService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_assignment_participant_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "non-participant@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course

        with (
            patch("src.routers.assignments.CoursePolicy.assert_course_access") as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = course_errors.ParticipantRoleRequiredError("non-participant@test.com", "course-123")
            await get_assignment("course-123", 10, mock_db, "non-participant@test.com")

        assert exc_info.value.status_code == 403

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.AssignmentService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_course_assignments_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()
        mock_assignments = [MagicMock(), MagicMock()]
        for i, ass in enumerate(mock_assignments):
            ass.course_id = "course-123"
            ass.assignment_id = i + 1
            ass.title = f"Assignment {i+1}"

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_course_assignments.return_value = mock_assignments

        with (
            patch("src.routers.assignments.CoursePolicy.assert_course_access") as mock_assert_access,
            patch("src.routers.assignments.Assignment.model_validate") as mock_validate
        ):
            mock_validate.side_effect = lambda x: {"course_id": x.course_id, "assignment_id": x.assignment_id, "title": x.title}
            result = await get_course_assignments("course-123", mock_db, "student@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_user, mock_course, mock_db)
        mock_assignment_service.get_course_assignments.assert_called_once_with(mock_course)
        assert mock_validate.call_count == 2

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.AssignmentService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_course_assignments_empty(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_user = MagicMock()
        mock_user.isadmin = False
        mock_course = MagicMock()
        mock_assignments = []

        mock_user_service.get_user.return_value = mock_user
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_course_assignments.return_value = mock_assignments

        with patch("src.routers.assignments.CoursePolicy.assert_course_access"):
            result = await get_course_assignments("course-123", mock_db, "student@test.com")

        assert result == []

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_course_assignments_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class,
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "user@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("user@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await get_course_assignments("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_course_assignments_course_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class,
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
            await get_course_assignments("course-123", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch("src.routers.assignments.UserService")
    @patch("src.routers.assignments.CourseService")
    @patch("src.routers.assignments.get_db")
    @patch("src.routers.assignments.get_current_user")
    async def test_get_course_assignments_participant_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_course_service_class,
        mock_user_service_class,
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

        with (
            patch("src.routers.assignments.CoursePolicy.assert_course_access") as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = course_errors.ParticipantRoleRequiredError("non-participant@test.com", "course-123")
            await get_course_assignments("course-123", mock_db, "non-participant@test.com")

        assert exc_info.value.status_code == 403
