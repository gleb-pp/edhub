from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import assignments as assignment_errors
from src.exceptions import courses as course_errors
from src.exceptions import students as student_errors
from src.exceptions import submissions as submission_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.models.common import Success
from src.routers.grades import get_submission_grade, grade_submission

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user_service():
    with patch("src.routers.grades.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service():
    with patch("src.routers.grades.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_assignment_service():
    with patch("src.routers.grades.AssignmentService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_submission_service():
    with patch("src.routers.grades.SubmissionService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_grade_service():
    with patch("src.routers.grades.GradeService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user():
    with patch("src.routers.grades.get_current_user") as mock_func:
        yield mock_func


@pytest.fixture
def mock_teacher():
    teacher = MagicMock()
    teacher.isadmin = False
    teacher.email = "teacher@test.com"
    return teacher


@pytest.fixture
def mock_student():
    student = MagicMock()
    student.email = "student@test.com"
    return student


@pytest.fixture
def mock_course():
    course = MagicMock()
    course.course_id = "course-123"
    return course


@pytest.fixture
def mock_assignment():
    assignment = MagicMock()
    assignment.assignment_id = 10
    return assignment


@pytest.fixture
def mock_submission():
    return MagicMock()


@pytest.fixture
def mock_grade():
    grade = MagicMock()
    grade.course_id = "course-123"
    grade.assignment_id = 10
    grade.student_email = "student@test.com"
    grade.grade = 85
    return grade


class TestGradesRouter:

    @pytest.mark.parametrize(
        "comment,expected_comment",
        [
            ("Good job!", "Good job!"),
            (None, None),
        ],
        ids=["with_comment", "without_comment"],
    )
    async def test_grade_submission_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_grade_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_course,
        mock_assignment,
        mock_submission,
        comment,
        expected_comment,
    ) -> None:
        mock_get_current_user.return_value = "teacher@test.com"
        mock_user_service.get_user.side_effect = [mock_teacher, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission

        with (
            patch("src.routers.grades.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.grades.StudentPolicy.assert_student_access") as mock_assert_student,
        ):
            result = await grade_submission(
                mock_course.course_id,
                mock_assignment.assignment_id,
                mock_student.email,
                85,
                mock_db,
                "teacher@test.com",
                comment,
            )

        assert isinstance(result, Success)
        assert result.success is True

        mock_user_service.get_user.assert_any_call("teacher@test.com")
        mock_user_service.get_user.assert_any_call(mock_student.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, mock_assignment.assignment_id)
        mock_submission_service.get_submission.assert_called_once_with(mock_assignment, mock_student)
        mock_grade_service.update_submission_grade.assert_called_once_with(
            mock_submission, 85, expected_comment, mock_teacher,
        )
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_call_policies",
        [
            ("teacher_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("student_not_found", [MagicMock(), user_errors.UserNotFoundError("student@test.com")], 404, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
            ("student_role_required", student_errors.StudentRoleRequiredError("not-a-student@test.com", "course-123"), 400, True),
            ("assignment_not_found", assignment_errors.AssignmentNotFoundError("course-123", 999), 400, True),
            ("submission_not_found", submission_errors.SubmissionNotFoundError("course-123", 10, "student@test.com"), 400, True),
        ],
        ids=[
            "teacher_not_found",
            "student_not_found",
            "course_not_found",
            "teacher_role_required",
            "student_role_required",
            "assignment_not_found",
            "submission_not_found",
        ],
    )
    async def test_grade_submission_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_grade_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_call_policies,
    ) -> None:
        mock_get_current_user.return_value = "teacher@test.com"

        if error_scenario == "teacher_not_found" or error_scenario == "student_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_teacher, mock_student]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "assignment_not_found":
            mock_assignment_service.get_assignment.side_effect = side_effect
        else:
            mock_assignment_service.get_assignment.return_value = MagicMock()

        if error_scenario == "submission_not_found":
            mock_submission_service.get_submission.side_effect = side_effect
        else:
            mock_submission_service.get_submission.return_value = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            if error_scenario in ["teacher_role_required", "student_role_required"]:
                with (
                    patch("src.routers.grades.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
                    patch("src.routers.grades.StudentPolicy.assert_student_access") as mock_assert_student,
                ):
                    if error_scenario == "teacher_role_required":
                        mock_assert_teacher.side_effect = side_effect
                    else:
                        mock_assert_student.side_effect = side_effect

                    await grade_submission(
                        mock_course.course_id,
                        10,
                        "student@test.com" if error_scenario != "student_role_required" else "not-a-student@test.com",
                        85,
                        mock_db,
                        "teacher@test.com",
                        None,
                    )
            else:
                with (
                    patch("src.routers.grades.TeacherPolicy.assert_teacher_access"),
                    patch("src.routers.grades.StudentPolicy.assert_student_access"),
                ):
                    await grade_submission(
                        mock_course.course_id,
                        10,
                        "student@test.com",
                        85,
                        mock_db,
                        "teacher@test.com",
                        None,
                    )

        assert exc_info.value.status_code == expected_status
        mock_db.commit.assert_not_called()

        mock_grade_service.update_submission_grade.assert_not_called()

    @pytest.mark.parametrize(
        "user_role,user_email",
        [
            ("teacher", "teacher@test.com"),
            ("student", "student@test.com"),
            ("parent", "parent@test.com"),
        ],
        ids=["as_teacher", "as_student", "as_parent"],
    )
    async def test_get_submission_grade_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_grade_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_course,
        mock_assignment,
        mock_submission,
        mock_grade,
        user_role,
        user_email,
    ) -> None:
        mock_get_current_user.return_value = user_email

        mock_user = mock_teacher if user_role == "teacher" else MagicMock()
        mock_user.email = user_email

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission
        mock_grade_service.get_submission_grade.return_value = mock_grade

        with (
            patch("src.routers.grades.StudentPolicy.assert_access_to_student") as mock_assert_access,
            patch("src.routers.grades.AssignmentGrade.model_validate") as mock_validate,
        ):
            expected_result = {"grade": 85}
            mock_validate.return_value = expected_result
            result = await get_submission_grade(
                mock_course.course_id,
                mock_assignment.assignment_id,
                mock_student.email,
                mock_db,
                user_email,
            )

        assert result == expected_result
        mock_user_service.get_user.assert_any_call(user_email)
        mock_user_service.get_user.assert_any_call(mock_student.email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_access.assert_called_once_with(mock_student, mock_user, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, mock_assignment.assignment_id)
        mock_submission_service.get_submission.assert_called_once_with(mock_assignment, mock_student)
        mock_grade_service.get_submission_grade.assert_called_once_with(mock_submission)
        mock_validate.assert_called_once_with(mock_grade)

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_access",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("student_not_found", [MagicMock(), user_errors.UserNotFoundError("student@test.com")], 400, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, True),
            ("assignment_not_found", assignment_errors.AssignmentNotFoundError("course-123", 999), 400, True),
            ("submission_not_found", submission_errors.SubmissionNotFoundError("course-123", 10, "student@test.com"), 400, True),
            ("grade_not_found", submission_errors.GradeNotFoundError("course-123", 10, "student@test.com"), 404, True),
            ("access_denied", student_errors.NoAccessToStudentInfoError("student@test.com", "stranger@test.com", "course-123"), 403, True),
        ],
        ids=[
            "user_not_found",
            "student_not_found",
            "course_not_found",
            "assignment_not_found",
            "submission_not_found",
            "grade_not_found",
            "access_denied",
        ],
    )
    async def test_get_submission_grade_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_grade_service,
        mock_get_current_user,
        mock_student,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_access,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found" or error_scenario == "student_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [MagicMock(), mock_student]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "assignment_not_found":
            mock_assignment_service.get_assignment.side_effect = side_effect
        else:
            mock_assignment_service.get_assignment.return_value = MagicMock()

        if error_scenario == "submission_not_found":
            mock_submission_service.get_submission.side_effect = side_effect
        else:
            mock_submission_service.get_submission.return_value = MagicMock()

        if error_scenario == "grade_not_found":
            mock_grade_service.get_submission_grade.side_effect = side_effect

        with pytest.raises(HTTPException) as exc_info:
            if error_scenario == "access_denied":
                with patch("src.routers.grades.StudentPolicy.assert_access_to_student") as mock_assert_access:
                    mock_assert_access.side_effect = side_effect
                    await get_submission_grade(
                        mock_course.course_id,
                        10,
                        mock_student.email,
                        mock_db,
                        "user@test.com",
                    )
            else:
                with patch("src.routers.grades.StudentPolicy.assert_access_to_student"):
                    await get_submission_grade(
                        mock_course.course_id,
                        10,
                        mock_student.email,
                        mock_db,
                        "user@test.com",
                    )

        assert exc_info.value.status_code == expected_status

        with patch("src.routers.grades.AssignmentGrade.model_validate") as mock_validate:
            mock_validate.assert_not_called()
