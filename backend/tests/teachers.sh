#!/bin/bash
set -euo pipefail

API_URL="http://localhost:8000"

source ./backend/tests/common_functions.sh

# --------------------------------------------------------------------

success_test "Registration of Alice" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\",\"name\":\"Alice\"}"

# --------------------------------------------------------------------

success_test "Registration of Bob" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\",\"name\":\"Bob\"}"

# --------------------------------------------------------------------

success_test "Registration of Charlie" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"charlie@example.com\",\"password\":\"charliePass123!\",\"name\":\"Charlie\"}"

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

mathcourseid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_course?title=Math&organization=Innopolis%20University" | extract_field course_id)

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_user_role?course_id=$mathcourseid")

expected='
    {"is_instructor":true,"is_teacher":true,"is_student":false,"is_parent":false,"is_admin":false}
'

json_exact_match_test "Get the Alice's role in course Math" "$info" "$expected" "is_instructor"

# --------------------------------------------------------------------

success_test "Invite Bob to Alice's course as a teacher" \
    -X POST "$API_URL/invite_teacher?course_id=$mathcourseid&new_teacher_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Invite Charlie to Alice's course as a student" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_enrolled_students?course_id=$mathcourseid")

expected='[
    {"email":"charlie@example.com","name":"Charlie"}
]'

json_exact_match_test "Get students enrolled into Math course by Alice" "$info" "$expected" "email"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_teachers?course_id=$mathcourseid")

expected='[
    {"email":"bob@example.com","name":"Bob"}
]'

json_exact_match_test "Get Math course teachers by Alice" "$info" "$expected" "email"

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_user_role?course_id=$mathcourseid")

expected='
  {"is_instructor":false,"is_teacher":true,"is_student":false,"is_parent":false,"is_admin":false}
'

json_exact_match_test "Get the Bob's role in course Math" "$info" "$expected" "is_instructor"

# --------------------------------------------------------------------

success_test "Request to remove Charlie from Math course by Bob" \
    -X DELETE "$API_URL/remove_student?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_enrolled_students?course_id=$mathcourseid")

expected='[
]'

json_exact_match_test "Get students enrolled into Math course by Bob" "$info" "$expected" "email"

# --------------------------------------------------------------------

success_test "Invite Charlie to Alice's course as a student" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request to remove Alice from Math course by Bob" \
    -X DELETE "$API_URL/remove_teacher?course_id=$mathcourseid&removing_teacher_email=alice@example.com" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to change the course instructor from Alice to Bob by Bob" \
    -X PATCH "$API_URL/change_course_instructor?course_id=$mathcourseid&teacher_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

assignmentid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_assignment?course_id=$mathcourseid&section_id=1&title=Assignment%201&description=To%20do%20exercise%2010%20from%20the%20course%20book" | extract_field assignment_id)

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

fail_test "Request to remove Alice from Math course by Alice" \
    -X DELETE "$API_URL/remove_teacher?course_id=$mathcourseid&removing_teacher_email=alice@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

success_test "Change the course instructor from Alice to Bob by Alice" \
    -X PATCH "$API_URL/change_course_instructor?course_id=$mathcourseid&teacher_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Request to remove Alice from Math course by Alice" \
    -X DELETE "$API_URL/remove_teacher?course_id=$mathcourseid&removing_teacher_email=alice@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Removing Alice's account from Alice" \
    -X DELETE "$API_URL/remove_user?deleted_user_email=alice@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_user_role?course_id=$mathcourseid")

expected='
  {"is_instructor":true,"is_teacher":true,"is_student":false,"is_parent":false,"is_admin":false}
'

json_exact_match_test "Get the Bob's role in course Math" "$info" "$expected" "is_instructor"

# --------------------------------------------------------------------

./backend/tests/dbreset.sh || exit 1
