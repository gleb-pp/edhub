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

success_test "Registration of Dmitry" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"dmitry@example.com\",\"password\":\"dmitryPass123!\",\"name\":\"Dmitry\"}"

# --------------------------------------------------------------------

success_test "Registration of Eugene" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"eugene@example.com\",\"password\":\"eugenePass123!\",\"name\":\"Eugene\"}"

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

mathcourseid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_course?title=Math&organization=Innopolis%20University" | extract_field course_id)

success_test "Invite Bob to Alice's course as a teacher" \
    -X POST "$API_URL/invite_teacher?course_id=$mathcourseid&new_teacher_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to invite Dmitry to Alice's course as a Charlie's parent (Charlie is not enrolled)" \
    -X POST "$API_URL/invite_parent?course_id=$mathcourseid&student_email=charlie@example.com&parent_email=dmitry@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Invite Charlie to Alice's course as a student" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Invite Dmitry to Alice's course as a Charlie's parent" \
    -X POST "$API_URL/invite_parent?course_id=$mathcourseid&student_email=charlie@example.com&parent_email=dmitry@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

success_test "Invite Eugene to Alice's course as a Charlie's parent" \
    -X POST "$API_URL/invite_parent?course_id=$mathcourseid&student_email=charlie@example.com&parent_email=eugene@example.com" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to invite Dmitry to Alice's course as a Charlie's parent one more time" \
    -X POST "$API_URL/invite_parent?course_id=$mathcourseid&student_email=charlie@example.com&parent_email=dmitry@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_students_parents?course_id=$mathcourseid&student_email=charlie@example.com")

expected='[
    {"email":"dmitry@example.com","name":"Dmitry"},
    {"email":"eugene@example.com","name":"Eugene"}
]'

json_exact_match_test "Get the list of Charlie's parents" "$info" "$expected" "email"

# --------------------------------------------------------------------

success_test "Remove Dmitry from the Alice's course as a Charlie's parent" \
    -X DELETE "$API_URL/remove_parent?course_id=$mathcourseid&student_email=charlie@example.com&parent_email=dmitry@example.com" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "One more time remove Dmitry from the Alice's course as a Charlie's parent" \
    -X DELETE "$API_URL/remove_parent?course_id=$mathcourseid&student_email=charlie@example.com&parent_email=dmitry@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Invite Dmitry to Alice's course as a student" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=dmitry@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Invite Eugene to Alice's course as a Dmitry's parent" \
    -X POST "$API_URL/invite_parent?course_id=$mathcourseid&student_email=dmitry@example.com&parent_email=eugene@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_parents_children?course_id=$mathcourseid&parent_email=eugene@example.com")

expected='[
    {"email":"dmitry@example.com","name":"Dmitry"},
    {"email":"charlie@example.com","name":"Charlie"}
]'

json_exact_match_test "Get the list of Eugene's children" "$info" "$expected" "email"

# --------------------------------------------------------------------

login_and_get_token "Login as Eugene" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"eugene@example.com\",\"password\":\"eugenePass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_user_role?course_id=$mathcourseid")

expected='
    {"is_instructor":false,"is_teacher":false,"is_student":false,"is_parent":true,"is_admin":false}
'

json_exact_match_test "Get the Eugene's role in course Math" "$info" "$expected" "is_instructor"

# --------------------------------------------------------------------

./backend/tests/dbreset.sh || exit 1
