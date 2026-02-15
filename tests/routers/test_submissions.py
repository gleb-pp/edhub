import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.submissions import (
    submit_assignment,
    get_assignment_submissions,
    get_submission
)
from src.exceptions import assignments as assignment_errors
from src.exceptions import courses as course_errors
from src.exceptions import students as student_errors
from src.exceptions import submissions as submission_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success


pytestmark = pytest.mark.asyncio


class TestSubmissionsRouter:

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.AssignmentService')
    @patch('src.routers.submissions.SubmissionService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_submit_assignment_update_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_submission_service_class,
        mock_assignment_service_class,
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
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service
        mock_submission_service = MagicMock()
        mock_submission_service_class.return_value = mock_submission_service

        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()

        mock_user_service.get_user.return_value = mock_student
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission

        with (
            patch('src.routers.submissions.StudentPolicy.assert_student_access') as mock_assert_student,
            patch('src.routers.submissions.GradePolicy.assert_not_graded') as mock_assert_not_graded
        ):
            result = await submit_assignment(
                "course-123", 10, mock_db, "Test submission", "student@test.com"
            )

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, 10)
        mock_submission_service.get_submission.assert_called_once_with(mock_assignment, mock_student)
        mock_assert_not_graded.assert_called_once_with(mock_submission, mock_db)
        mock_submission_service.update_submission.assert_called_once_with(mock_submission, "Test submission")
        mock_db.commit.assert_called_once()

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.AssignmentService')
    @patch('src.routers.submissions.SubmissionService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_submit_assignment_create_new(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_submission_service_class,
        mock_assignment_service_class,
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
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service
        mock_submission_service = MagicMock()
        mock_submission_service_class.return_value = mock_submission_service

        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()

        mock_user_service.get_user.return_value = mock_student
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.side_effect = submission_errors.SubmissionNotFoundError(
            "course-123", 10, "student@test.com"
        )

        with patch('src.routers.submissions.StudentPolicy.assert_student_access'):
            result = await submit_assignment(
                "course-123", 10, mock_db, "Test submission", "student@test.com"
            )

        assert result.success is True
        mock_submission_service.create_submission.assert_called_once_with(
            mock_assignment, mock_student, "Test submission"
        )
        mock_db.commit.assert_called_once()

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_submit_assignment_user_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("student@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await submit_assignment(
                "course-123", 10, mock_db, "Test submission", "student@test.com"
            )

        assert exc_info.value.status_code == 401

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_submit_assignment_course_not_found(
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

        mock_student = MagicMock()
        mock_user_service.get_user.return_value = mock_student
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await submit_assignment(
                "course-123", 10, mock_db, "Test submission", "student@test.com"
            )

        assert exc_info.value.status_code == 400

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.AssignmentService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_submit_assignment_student_role_required(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
        mock_course_service_class,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "non-student@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_course_service = MagicMock()
        mock_course_service_class.return_value = mock_course_service
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_student = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.return_value = mock_student
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.submissions.StudentPolicy.assert_student_access') as mock_assert_student,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_student.side_effect = student_errors.StudentRoleRequiredError("non-student@test.com", "course-123")
            await submit_assignment(
                "course-123", 10, mock_db, "Test submission", "non-student@test.com"
            )

        assert exc_info.value.status_code == 403

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.AssignmentService')
    @patch('src.routers.submissions.SubmissionService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_submit_assignment_graded(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_submission_service_class,
        mock_assignment_service_class,
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
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service
        mock_submission_service = MagicMock()
        mock_submission_service_class.return_value = mock_submission_service

        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()

        mock_user_service.get_user.return_value = mock_student
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission

        with (
            patch('src.routers.submissions.StudentPolicy.assert_student_access'),
            patch('src.routers.submissions.GradePolicy.assert_not_graded') as mock_assert_not_graded,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_not_graded.side_effect = submission_errors.SubmissionGradedError("course-123", 10, "student@test.com")
            await submit_assignment(
                "course-123", 10, mock_db, "Test submission", "student@test.com"
            )

        assert exc_info.value.status_code == 409

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.AssignmentService')
    @patch('src.routers.submissions.SubmissionService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_assignment_submissions_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_submission_service_class,
        mock_assignment_service_class,
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
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service
        mock_submission_service = MagicMock()
        mock_submission_service_class.return_value = mock_submission_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_submissions = [MagicMock(), MagicMock()]

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_assignment_submissions.return_value = mock_submissions

        with (
            patch('src.routers.submissions.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            patch('src.routers.submissions.Submission.model_validate') as mock_validate
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_assignment_submissions("course-123", 10, mock_db, "teacher@test.com")

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with("teacher@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, 10)
        mock_submission_service.get_assignment_submissions.assert_called_once_with(mock_assignment)
        assert mock_validate.call_count == 2

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_assignment_submissions_user_not_found(
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
            await get_assignment_submissions("course-123", 10, mock_db, "teacher@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_assignment_submissions_teacher_role_required(
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

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.submissions.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123")
            await get_assignment_submissions("course-123", 10, mock_db, "student@test.com")

        assert exc_info.value.status_code == 403

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.AssignmentService')
    @patch('src.routers.submissions.SubmissionService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_submission_as_teacher(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_submission_service_class,
        mock_assignment_service_class,
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
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service
        mock_submission_service = MagicMock()
        mock_submission_service_class.return_value = mock_submission_service

        mock_teacher = MagicMock()
        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()
        mock_submission.submission_text = "Test submission"

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission

        with (
            patch('src.routers.submissions.StudentPolicy.assert_access_to_student') as mock_assert_access,
            patch('src.routers.submissions.Submission.model_validate') as mock_validate
        ):
            expected_result = {"submission_text": "Test submission"}
            mock_validate.return_value = expected_result
            result = await get_submission(
                "course-123", 10, "student@test.com", mock_db, "teacher@test.com"
            )

        assert result == expected_result
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_student, mock_teacher, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, 10)
        mock_submission_service.get_submission.assert_called_once_with(mock_assignment, mock_student)
        mock_validate.assert_called_once_with(mock_submission)

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.AssignmentService')
    @patch('src.routers.submissions.SubmissionService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_submission_as_student(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_submission_service_class,
        mock_assignment_service_class,
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
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service
        mock_submission_service = MagicMock()
        mock_submission_service_class.return_value = mock_submission_service

        mock_user = MagicMock()
        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission

        with (
            patch('src.routers.submissions.StudentPolicy.assert_access_to_student'),
            patch('src.routers.submissions.Submission.model_validate')
        ):
            await get_submission(
                "course-123", 10, "student@test.com", mock_db, "student@test.com"
            )

        mock_user_service.get_user.assert_any_call("student@test.com")
        mock_user_service.get_user.assert_any_call("student@test.com")

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_submission_user_not_found(
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
            await get_submission("course-123", 10, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_submission_student_not_found(
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
        mock_user_service.get_user.side_effect = [
            MagicMock(),  # user
            user_errors.UserNotFoundError("student@test.com")  # student
        ]

        with pytest.raises(HTTPException) as exc_info:
            await get_submission("course-123", 10, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_submission_course_not_found(
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
            await get_submission("course-123", 10, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.AssignmentService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_submission_submission_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_assignment_service_class,
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
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service

        mock_user = MagicMock()
        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment

        with (
            patch('src.routers.submissions.StudentPolicy.assert_access_to_student'),
            patch('src.routers.submissions.SubmissionService') as mock_submission_service_class
        ):
            mock_submission_service = MagicMock()
            mock_submission_service_class.return_value = mock_submission_service
            mock_submission_service.get_submission.side_effect = submission_errors.SubmissionNotFoundError(
                "course-123", 10, "student@test.com"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await get_submission("course-123", 10, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 404

    @patch('src.routers.submissions.UserService')
    @patch('src.routers.submissions.CourseService')
    @patch('src.routers.submissions.get_db')
    @patch('src.routers.submissions.get_current_user')
    async def test_get_submission_access_denied(
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
        mock_student = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.submissions.StudentPolicy.assert_access_to_student') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = student_errors.NoAccessToStudentInfoError(
                "student@test.com", "stranger@test.com", "course-123"
            )
            await get_submission("course-123", 10, "student@test.com", mock_db, "stranger@test.com")

        assert exc_info.value.status_code == 403
