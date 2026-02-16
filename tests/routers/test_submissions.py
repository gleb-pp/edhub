from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.exceptions import assignments as assignment_errors
from src.exceptions import courses as course_errors
from src.exceptions import students as student_errors
from src.exceptions import submissions as submission_errors
from src.exceptions import teachers as teacher_errors
from src.exceptions import users as user_errors
from src.routers.submissions import (
    get_assignment_submissions,
    get_submission,
    submit_assignment,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user_service():
    with patch("src.routers.submissions.UserService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_course_service():
    with patch("src.routers.submissions.CourseService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_assignment_service():
    with patch("src.routers.submissions.AssignmentService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_submission_service():
    with patch("src.routers.submissions.SubmissionService") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_get_current_user():
    with patch("src.routers.submissions.get_current_user") as mock_func:
        yield mock_func


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.isadmin = False
    user.email = "user@test.com"
    return user


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
    submission = MagicMock()
    submission.submission_text = "Test submission"
    return submission


class TestSubmissionsRouter:

    @pytest.mark.parametrize(
        "scenario,get_submission_effect,expected_method",
        [
            ("update", MagicMock(), "update_submission"),
            ("create", submission_errors.SubmissionNotFoundError("course-123", 10, "student@test.com"), "create_submission"),
        ],
        ids=["update_existing", "create_new"],
    )
    async def test_submit_assignment_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_get_current_user,
        mock_student,
        mock_course,
        mock_assignment,
        mock_submission,
        scenario,
        get_submission_effect,
        expected_method,
    ) -> None:
        mock_get_current_user.return_value = "student@test.com"
        mock_user_service.get_user.return_value = mock_student
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment

        if scenario == "update":
            mock_submission_service.get_submission.return_value = mock_submission
        else:
            mock_submission_service.get_submission.side_effect = get_submission_effect

        with (
            patch("src.routers.submissions.StudentPolicy.assert_student_access") as mock_assert_student,
            patch("src.routers.submissions.GradePolicy.assert_not_graded") as mock_assert_not_graded,
        ):
            result = await submit_assignment(
                mock_course.course_id,
                mock_assignment.assignment_id,
                mock_db,
                "Test submission",
                "student@test.com",
            )

        assert result.success is True
        mock_user_service.get_user.assert_called_once_with("student@test.com")
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assert_student.assert_called_once_with(mock_student, mock_course, mock_db)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, mock_assignment.assignment_id)

        if scenario == "update":
            mock_submission_service.get_submission.assert_called_once_with(mock_assignment, mock_student)
            mock_assert_not_graded.assert_called_once_with(mock_submission, mock_db)
            mock_submission_service.update_submission.assert_called_once_with(mock_submission, "Test submission")
            mock_submission_service.create_submission.assert_not_called()
        else:
            mock_submission_service.get_submission.assert_called_once_with(mock_assignment, mock_student)
            mock_assert_not_graded.assert_not_called()
            mock_submission_service.create_submission.assert_called_once_with(
                mock_assignment, mock_student, "Test submission",
            )
            mock_submission_service.update_submission.assert_not_called()

        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policies",
        [
            ("user_not_found", user_errors.UserNotFoundError("student@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, True),
            ("assignment_not_found", assignment_errors.AssignmentNotFoundError("course-123", 10), 400, True),
            ("student_role_required", student_errors.StudentRoleRequiredError("non-student@test.com", "course-123"), 403, True),
            ("submission_graded", submission_errors.SubmissionGradedError("course-123", 10, "student@test.com"), 409, True),
        ],
        ids=["user_not_found", "course_not_found", "assignment_not_found", "student_role_required", "submission_graded"],
    )
    async def test_submit_assignment_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_get_current_user,
        mock_student,
        mock_course,
        mock_assignment,
        mock_submission,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policies,
    ) -> None:
        mock_get_current_user.return_value = "student@test.com"

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_student

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "assignment_not_found":
            mock_assignment_service.get_assignment.side_effect = side_effect
        else:
            mock_assignment_service.get_assignment.return_value = mock_assignment

        if error_scenario not in ["user_not_found", "course_not_found", "assignment_not_found"]:
            mock_submission_service.get_submission.return_value = mock_submission

        with (
            patch("src.routers.submissions.StudentPolicy.assert_student_access") as mock_assert_student,
            patch("src.routers.submissions.GradePolicy.assert_not_graded") as mock_assert_not_graded,
        ):
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "student_role_required":
                    mock_assert_student.side_effect = side_effect
                elif error_scenario == "submission_graded":
                    mock_assert_not_graded.side_effect = side_effect

                await submit_assignment(
                    mock_course.course_id,
                    mock_assignment.assignment_id,
                    mock_db,
                    "Test submission",
                    "student@test.com",
                )

            assert exc_info.value.status_code == expected_status

        mock_db.commit.assert_not_called()
        mock_submission_service.update_submission.assert_not_called()
        mock_submission_service.create_submission.assert_not_called()

    @pytest.mark.parametrize(
        "user_email,is_admin,should_check_teacher",
        [
            ("teacher@test.com", False, True),
            ("admin@test.com", True, False),
        ],
        ids=["as_teacher", "as_admin"],
    )
    async def test_get_assignment_submissions_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_get_current_user,
        mock_teacher,
        mock_course,
        mock_assignment,
        user_email,
        is_admin,
        should_check_teacher,
    ) -> None:
        mock_get_current_user.return_value = user_email
        mock_teacher.isadmin = is_admin
        mock_teacher.email = user_email

        mock_user_service.get_user.return_value = mock_teacher
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment

        mock_submissions = [MagicMock(), MagicMock()]
        mock_submission_service.get_assignment_submissions.return_value = mock_submissions

        with (
            patch("src.routers.submissions.TeacherPolicy.assert_teacher_access") as mock_assert_teacher,
            patch("src.routers.submissions.Submission.model_validate") as mock_validate,
        ):
            mock_validate.side_effect = lambda x: f"validated_{x}"
            result = await get_assignment_submissions(
                mock_course.course_id, mock_assignment.assignment_id, mock_db, user_email,
            )

        assert len(result) == 2
        mock_user_service.get_user.assert_called_once_with(user_email)
        mock_course_service.get_course.assert_called_once_with(mock_course.course_id)
        mock_assignment_service.get_assignment.assert_called_once_with(mock_course, mock_assignment.assignment_id)
        mock_submission_service.get_assignment_submissions.assert_called_once_with(mock_assignment)
        assert mock_validate.call_count == 2

        if should_check_teacher:
            mock_assert_teacher.assert_called_once_with(mock_teacher, mock_course, mock_db)
        else:
            mock_assert_teacher.assert_not_called()

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_policy",
        [
            ("user_not_found", user_errors.UserNotFoundError("teacher@test.com"), 401, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("assignment_not_found", assignment_errors.AssignmentNotFoundError("course-123", 10), 400, True),
            ("teacher_role_required", teacher_errors.TeacherRoleRequiredError("student@test.com", "course-123"), 403, True),
        ],
        ids=["user_not_found", "course_not_found", "assignment_not_found", "teacher_role_required"],
    )
    async def test_get_assignment_submissions_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_get_current_user,
        mock_teacher,
        mock_course,
        error_scenario,
        side_effect,
        expected_status,
        should_check_policy,
    ) -> None:
        mock_get_current_user.return_value = "teacher@test.com"
        mock_teacher.isadmin = False

        if error_scenario == "user_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.return_value = mock_teacher

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "assignment_not_found":
            mock_assignment_service.get_assignment.side_effect = side_effect
        else:
            mock_assignment_service.get_assignment.return_value = MagicMock()

        with patch("src.routers.submissions.TeacherPolicy.assert_teacher_access") as mock_assert_teacher:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "teacher_role_required":
                    mock_assert_teacher.side_effect = side_effect

                await get_assignment_submissions(
                    mock_course.course_id, 10, mock_db, "teacher@test.com",
                )

            assert exc_info.value.status_code == expected_status

            if should_check_policy:
                mock_assert_teacher.assert_called_once()
            else:
                mock_assert_teacher.assert_not_called()

    @pytest.mark.parametrize(
        "user_role,user_email",
        [
            ("teacher", "teacher@test.com"),
            ("student", "student@test.com"),
        ],
        ids=["as_teacher", "as_student"],
    )
    async def test_get_submission_success(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_get_current_user,
        mock_teacher,
        mock_student,
        mock_course,
        mock_assignment,
        mock_submission,
        user_role,
        user_email,
    ) -> None:
        mock_get_current_user.return_value = user_email

        mock_user = mock_teacher if user_role == "teacher" else mock_student
        mock_user.email = user_email

        mock_user_service.get_user.side_effect = [mock_user, mock_student]
        mock_course_service.get_course.return_value = mock_course
        mock_assignment_service.get_assignment.return_value = mock_assignment
        mock_submission_service.get_submission.return_value = mock_submission

        with (
            patch("src.routers.submissions.StudentPolicy.assert_access_to_student") as mock_assert_access,
            patch("src.routers.submissions.Submission.model_validate") as mock_validate,
        ):
            expected_result = {"submission_text": "Test submission"}
            mock_validate.return_value = expected_result
            result = await get_submission(
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
        mock_validate.assert_called_once_with(mock_submission)

    @pytest.mark.parametrize(
        "error_scenario,side_effect,expected_status,should_check_access",
        [
            ("user_not_found", user_errors.UserNotFoundError("user@test.com"), 401, False),
            ("student_not_found", [MagicMock(), user_errors.UserNotFoundError("student@test.com")], 400, False),
            ("course_not_found", course_errors.CourseNotFoundError("course-123"), 400, False),
            ("assignment_not_found", assignment_errors.AssignmentNotFoundError("course-123", 10), 400, True),
            ("submission_not_found", submission_errors.SubmissionNotFoundError("course-123", 10, "student@test.com"), 404, True),
            ("access_denied", student_errors.NoAccessToStudentInfoError("student@test.com", "stranger@test.com", "course-123"), 403, True),
        ],
        ids=[
            "user_not_found",
            "student_not_found",
            "course_not_found",
            "assignment_not_found",
            "submission_not_found",
            "access_denied",
        ],
    )
    async def test_get_submission_errors(
        self,
        mock_db,
        mock_user_service,
        mock_course_service,
        mock_assignment_service,
        mock_submission_service,
        mock_get_current_user,
        mock_user,
        mock_student,
        mock_course,
        mock_assignment,
        error_scenario,
        side_effect,
        expected_status,
        should_check_access,
    ) -> None:
        mock_get_current_user.return_value = "user@test.com"

        if error_scenario == "user_not_found" or error_scenario == "student_not_found":
            mock_user_service.get_user.side_effect = side_effect
        else:
            mock_user_service.get_user.side_effect = [mock_user, mock_student]

        if error_scenario == "course_not_found":
            mock_course_service.get_course.side_effect = side_effect
        else:
            mock_course_service.get_course.return_value = mock_course

        if error_scenario == "assignment_not_found":
            mock_assignment_service.get_assignment.side_effect = side_effect
        else:
            mock_assignment_service.get_assignment.return_value = mock_assignment

        if error_scenario == "submission_not_found":
            mock_submission_service.get_submission.side_effect = side_effect
        else:
            mock_submission_service.get_submission.return_value = MagicMock()

        with patch("src.routers.submissions.StudentPolicy.assert_access_to_student") as mock_assert_access:
            with pytest.raises(HTTPException) as exc_info:
                if error_scenario == "access_denied":
                    mock_assert_access.side_effect = side_effect

                await get_submission(
                    mock_course.course_id,
                    mock_assignment.assignment_id,
                    mock_student.email,
                    mock_db,
                    "user@test.com",
                )

            assert exc_info.value.status_code == expected_status

            if should_check_access:
                mock_assert_access.assert_called_once()
            else:
                mock_assert_access.assert_not_called()

        with patch("src.routers.submissions.Submission.model_validate") as mock_validate:
            mock_validate.assert_not_called()
