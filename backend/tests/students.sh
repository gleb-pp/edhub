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

success_test "Invite Bob to Alice's course" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Invite Charlie to Alice's course" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_enrolled_students?course_id=$mathcourseid")

expected='[
    {"email":"bob@example.com","name":"Bob"},
    {"email":"charlie@example.com","name":"Charlie"}
]'

json_exact_match_test "Get students enrolled into Math course by Alice" "$info" "$expected" "email"

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

# --------------------------------------------------------------------

courses=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/available_courses")

expected='[
    {"course_id":"'"$mathcourseid"'","title":"Math","organization":"Innopolis University","instructor_email":"alice@example.com","instructor_name":"Alice"}
]'

json_partial_match_test "Request the list of available courses from Bob" "$courses" "$expected" "course_id" "creation_time emoji_id"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_user_role?course_id=$mathcourseid")

expected='
    {"is_instructor":false,"is_teacher":false,"is_student":true,"is_parent":false,"is_admin":false}
'

json_exact_match_test "Get the Bob's role in course Math" "$info" "$expected" "is_instructor"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_enrolled_students?course_id=$mathcourseid")

expected='[
    {"email":"bob@example.com","name":"Bob"},
    {"email":"charlie@example.com","name":"Charlie"}
]'

json_exact_match_test "Get students enrolled into Math course by Bob" "$info" "$expected" "email"

# --------------------------------------------------------------------

fail_test "Request to create a material from a student Bob" \
    -X POST "$API_URL/create_material?course_id=$mathcourseid&section_id=1&title=Lecture%20material&description=Lecture%20material%20description" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create an assignment from a student Bob" \
    -X POST "$API_URL/create_assignment?course_id=$mathcourseid&section_id=1&title=Assignment%201&description=To%20do%20exercise%2010%20from%20the%20course%20book" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to remove Charlie from Math course by Bob" \
    -X POST "$API_URL/remove_student?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Request to remove Bob from Math course by Bob" \
    -X POST "$API_URL/remove_student?course_id=$mathcourseid&student_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

courses=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/available_courses")

expected='[
    
]'

json_exact_match_test "Request the empty list of available courses from Bob" "$courses" "$expected" "course_id"

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_enrolled_students?course_id=$mathcourseid")

expected='[
    {"email":"charlie@example.com","name":"Charlie"}
]'

json_exact_match_test "Get students enrolled into Math course by Alice" "$info" "$expected" "email"

# --------------------------------------------------------------------

success_test "Request to remove Charlie from Math course by Alice" \
    -X POST "$API_URL/remove_student?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_enrolled_students?course_id=$mathcourseid")

expected='[
]
'

json_exact_match_test "Get students enrolled into Math course by Alice" "$info" "$expected" "email"

# --------------------------------------------------------------------

success_test "Invite Charlie to Alice's course" \
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

login_and_get_token "Login as Charlie" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"charlie@example.com\",\"password\":\"charliePass123!\"}"

success_test "Removing Charlie's account from Charlie" \
    -X POST "$API_URL/remove_user?deleted_user_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_enrolled_students?course_id=$mathcourseid")

expected='[
]
'

json_exact_match_test "Get students enrolled into Math course by Alice" "$info" "$expected" "email"

# --------------------------------------------------------------------

./backend/tests/dbreset.sh || exit 1
