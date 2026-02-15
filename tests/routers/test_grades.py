import pytest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from src.routers.grades import grade_submission, get_submission_grade
from src.exceptions import assignments as assignment_errors
from src.exceptions import courses as course_errors
from src.exceptions import students as student_errors
from src.exceptions import submissions as submission_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success


pytestmark = pytest.mark.asyncio


class TestGradesRouter:

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.SubmissionService')
    @patch('src.routers.grades.GradeService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_grade_submission_success(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_grade_service_class,
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
        mock_grade_service = MagicMock()
        mock_grade_service_class.return_value = mock_grade_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_student = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission

        with (
            patch('src.routers.grades.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            patch('src.routers.grades.StudentPolicy.assert_student_access') as mock_assert_student
        ):
            result = await grade_submission(
                "course-123", 10, "student@test.com", 85, mock_db, "teacher@test.com", "Good job!"
            )

        assert isinstance(result, Success)
        assert result.success is True
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, 10)
        mock_submission_service.get_submission.assert_called_once_with(mock_assignment, mock_student)
        mock_grade_service.update_submission_grade.assert_called_once_with(
            mock_submission, 85, "Good job!", mock_teacher
        )
        mock_db.commit.assert_called_once()

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.SubmissionService')
    @patch('src.routers.grades.GradeService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_grade_submission_without_comment(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_grade_service_class,
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
        mock_grade_service = MagicMock()
        mock_grade_service_class.return_value = mock_grade_service

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_course = MagicMock()
        mock_student = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission

        with (
            patch('src.routers.grades.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.grades.StudentPolicy.assert_student_access')
        ):
            result = await grade_submission(
                "course-123", 10, "student@test.com", 90, mock_db, "teacher@test.com", None
            )

        assert result.success is True
        mock_grade_service.update_submission_grade.assert_called_once_with(
            mock_submission, 90, None, mock_teacher
        )

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_grade_submission_teacher_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = user_errors.UserNotFoundError("teacher@test.com")

        with pytest.raises(HTTPException) as exc_info:
            await grade_submission(
                "course-123", 10, "student@test.com", 85, mock_db, "teacher@test.com", None
            )

        assert exc_info.value.status_code == 401

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_grade_submission_student_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_user_service_class
    ):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_current_user.return_value = "teacher@test.com"

        mock_user_service = MagicMock()
        mock_user_service_class.return_value = mock_user_service
        mock_user_service.get_user.side_effect = [
            MagicMock(),  # teacher
            user_errors.UserNotFoundError("student@test.com")  # student
        ]

        with pytest.raises(HTTPException) as exc_info:
            await grade_submission(
                "course-123", 10, "student@test.com", 85, mock_db, "teacher@test.com", None
            )

        assert exc_info.value.status_code == 404

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_grade_submission_course_not_found(
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
        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.side_effect = course_errors.CourseNotFoundError("course-123")

        with pytest.raises(HTTPException) as exc_info:
            await grade_submission(
                "course-123", 10, "student@test.com", 85, mock_db, "teacher@test.com", None
            )

        assert exc_info.value.status_code == 400

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_grade_submission_teacher_role_required(
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
        mock_student = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.grades.TeacherPolicy.assert_teacher_access') as mock_assert_teacher,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_teacher.side_effect = teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123")
            await grade_submission(
                "course-123", 10, "student@test.com", 85, mock_db, "student@test.com", None
            )

        assert exc_info.value.status_code == 403

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_grade_submission_student_role_required(
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
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course

        with (
            patch('src.routers.grades.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.grades.StudentPolicy.assert_student_access') as mock_assert_student,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_student.side_effect = student_errors.StudentRoleRequiredError("not-a-student@test.com", "course-123")
            await grade_submission(
                "course-123", 10, "not-a-student@test.com", 85, mock_db, "teacher@test.com", None
            )

        assert exc_info.value.status_code == 400

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_grade_submission_assignment_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
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

        mock_teacher = MagicMock()
        mock_teacher.isadmin = False
        mock_student = MagicMock()
        mock_course = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.side_effect = assignment_errors.AssignmentNotFoundError("course-123", 999)

        with (
            patch('src.routers.grades.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.grades.StudentPolicy.assert_student_access'),
            pytest.raises(HTTPException) as exc_info
        ):
            await grade_submission(
                "course-123", 999, "student@test.com", 85, mock_db, "teacher@test.com", None
            )

        assert exc_info.value.status_code == 400

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.SubmissionService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_grade_submission_submission_not_found(
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
        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.side_effect = submission_errors.SubmissionNotFoundError(
            "course-123", 10, "student@test.com"
        )

        with (
            patch('src.routers.grades.TeacherPolicy.assert_teacher_access'),
            patch('src.routers.grades.StudentPolicy.assert_student_access'),
            pytest.raises(HTTPException) as exc_info
        ):
            await grade_submission(
                "course-123", 10, "student@test.com", 85, mock_db, "teacher@test.com", None
            )

        assert exc_info.value.status_code == 400

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.SubmissionService')
    @patch('src.routers.grades.GradeService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_as_teacher(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_grade_service_class,
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
        mock_grade_service = MagicMock()
        mock_grade_service_class.return_value = mock_grade_service

        mock_teacher = MagicMock()
        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()
        mock_grade = MagicMock()
        mock_grade.course_id = "course-123"
        mock_grade.assignment_id = 10
        mock_grade.student_email = "student@test.com"
        mock_grade.grade = 85

        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission
        mock_grade_service.get_submission_grade.return_value = mock_grade

        with (
            patch('src.routers.grades.StudentPolicy.assert_access_to_student') as mock_assert_access,
            patch('src.routers.grades.AssignmentGrade.model_validate') as mock_validate
        ):
            expected_result = {"grade": 85}
            mock_validate.return_value = expected_result
            result = await get_submission_grade(
                "course-123", 10, "student@test.com", mock_db, "teacher@test.com"
            )

        assert result == expected_result
        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call("student@test.com")
        mock_course_service.get_course.assert_called_once_with("course-123")
        mock_assert_access.assert_called_once_with(mock_student, mock_teacher, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, 10)
        mock_submission_service.get_submission.assert_called_once_with(mock_assignment, mock_student)
        mock_grade_service.get_submission_grade.assert_called_once_with(mock_submission)
        mock_validate.assert_called_once_with(mock_grade)

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.SubmissionService')
    @patch('src.routers.grades.GradeService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_as_student(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_grade_service_class,
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
        mock_grade_service = MagicMock()
        mock_grade_service_class.return_value = mock_grade_service

        mock_user = MagicMock()
        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()
        mock_grade = MagicMock()

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission
        mock_grade_service.get_submission_grade.return_value = mock_grade

        with (
            patch('src.routers.grades.StudentPolicy.assert_access_to_student') as mock_assert_access,
            patch('src.routers.grades.AssignmentGrade.model_validate') as mock_validate
        ):
            mock_validate.return_value = {"grade": 85}
            await get_submission_grade("course-123", 10, "student@test.com", mock_db, "student@test.com")

        mock_assert_access.assert_called_once_with(mock_student, mock_user, mock_course, mock_db)
        mock_validate.assert_called_once_with(mock_grade)

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.SubmissionService')
    @patch('src.routers.grades.GradeService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_as_parent(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_grade_service_class,
        mock_submission_service_class,
        mock_assignment_service_class,
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
        mock_assignment_service = MagicMock()
        mock_assignment_service_class.return_value = mock_assignment_service
        mock_submission_service = MagicMock()
        mock_submission_service_class.return_value = mock_submission_service
        mock_grade_service = MagicMock()
        mock_grade_service_class.return_value = mock_grade_service

        mock_parent = MagicMock()
        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()
        mock_grade = MagicMock()

        mock_user_service.get_user.side_effect = [mock_parent, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission
        mock_grade_service.get_submission_grade.return_value = mock_grade

        with (
            patch('src.routers.grades.StudentPolicy.assert_access_to_student') as mock_assert_access,
            patch('src.routers.grades.AssignmentGrade.model_validate') as mock_validate
        ):
            mock_validate.return_value = {"grade": 85}
            await get_submission_grade("course-123", 10, "student@test.com", mock_db, "parent@test.com")

        mock_assert_access.assert_called_once_with(mock_student, mock_parent, mock_course, mock_db)
        mock_validate.assert_called_once_with(mock_grade)

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_user_not_found(
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
            await get_submission_grade("course-123", 10, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 401

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_student_not_found(
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
            await get_submission_grade("course-123", 10, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_course_not_found(
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
            await get_submission_grade("course-123", 10, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_assignment_not_found(
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

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.side_effect = assignment_errors.AssignmentNotFoundError("course-123", 999)

        with (
            patch('src.routers.grades.StudentPolicy.assert_access_to_student'),
            pytest.raises(HTTPException) as exc_info
        ):
            await get_submission_grade("course-123", 999, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.SubmissionService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_submission_not_found(
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
        mock_get_current_user.return_value = "user@test.com"

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

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.side_effect = submission_errors.SubmissionNotFoundError(
            "course-123", 10, "student@test.com"
        )

        with (
            patch('src.routers.grades.StudentPolicy.assert_access_to_student'),
            pytest.raises(HTTPException) as exc_info
        ):
            await get_submission_grade("course-123", 10, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 400

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.AssignmentService')
    @patch('src.routers.grades.SubmissionService')
    @patch('src.routers.grades.GradeService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_grade_not_found(
        self,
        mock_get_current_user,
        mock_get_db,
        mock_grade_service_class,
        mock_submission_service_class,
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
        mock_submission_service = MagicMock()
        mock_submission_service_class.return_value = mock_submission_service
        mock_grade_service = MagicMock()
        mock_grade_service_class.return_value = mock_grade_service

        mock_user = MagicMock()
        mock_student = MagicMock()
        mock_course = MagicMock()
        mock_assignment = MagicMock()
        mock_submission = MagicMock()

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission
        mock_grade_service.get_submission_grade.side_effect = submission_errors.GradeNotFoundError(
            "course-123", 10, "student@test.com"
        )

        with (
            patch('src.routers.grades.StudentPolicy.assert_access_to_student'),
            pytest.raises(HTTPException) as exc_info
        ):
            await get_submission_grade("course-123", 10, "student@test.com", mock_db, "user@test.com")

        assert exc_info.value.status_code == 404

    @patch('src.routers.grades.UserService')
    @patch('src.routers.grades.CourseService')
    @patch('src.routers.grades.get_db')
    @patch('src.routers.grades.get_current_user')
    async def test_get_submission_grade_access_denied(
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
            patch('src.routers.grades.StudentPolicy.assert_access_to_student') as mock_assert_access,
            pytest.raises(HTTPException) as exc_info
        ):
            mock_assert_access.side_effect = student_errors.NoAccessToStudentInfoError(
                "student@test.com", "stranger@test.com", "course-123"
            )
            await get_submission_grade("course-123", 10, "student@test.com", mock_db, "stranger@test.com")

        assert exc_info.value.status_code == 403
