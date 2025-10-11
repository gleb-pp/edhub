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

firstassignmentid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_assignment?course_id=$mathcourseid&section_id=1&title=Assignment%201&description=To%20do%20exercise%2010%20from%20the%20course%20book" | extract_field assignment_id)

secondassignmentid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_assignment?course_id=$mathcourseid&section_id=1&title=Assignment%202&description=To%20do%20exercise%2020%20from%20the%20course%20book" | extract_field assignment_id)

# --------------------------------------------------------------------

success_test "Invite Bob to Alice's course as a student" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Invite Charlie to Alice's course as a student" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Invite Eugene to Alice's course as Bob's parent" \
    -X POST "$API_URL/invite_parent?course_id=$mathcourseid&student_email=bob@example.com&parent_email=eugene@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

success_test "Submit assignment as Bob" \
    -X PUT "$API_URL/submit_assignment?course_id=$mathcourseid&assignment_id=$firstassignmentid&submission_text=The%20answer%20is%2010" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_student_course_grades?course_id=$mathcourseid&student_email=bob@example.com")

expected='[
    {"assignment_name":"Assignment 1","assignment_id":'$firstassignmentid',"grade":null,"comment":null,"grader_name":null,"grader_email":null},
    {"assignment_name":"Assignment 2","assignment_id":'$secondassignmentid',"grade":null,"comment":null,"grader_name":null,"grader_email":null}
]'

json_exact_match_test "Request Bob's assignment grades from Bob" "$info" "$expected" "assignment_name"

# --------------------------------------------------------------------

fail_test "Request all course grades from Bob (student)" \
    -X POST "$API_URL/get_all_course_grades?course_id=$mathcourseid" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request Charlie's assignment grades from Bob" \
    -X POST "$API_URL/get_student_course_grades?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request Eugene's assignment grades from Bob" \
    -X POST "$API_URL/get_student_course_grades?course_id=$mathcourseid&student_email=eugene@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_all_course_grades?course_id=$mathcourseid")

expected='[
    {"name":"Bob","email":"bob@example.com","grades":[null,null]},
    {"name":"Charlie","email":"charlie@example.com","grades":[null,null]}
]'

json_exact_match_test "Request all course grades from Alice" "$info" "$expected" "email"

# --------------------------------------------------------------------

login_and_get_token "Login as Eugene" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"eugene@example.com\",\"password\":\"eugenePass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_student_course_grades?course_id=$mathcourseid&student_email=bob@example.com")

expected='[
    {"assignment_name":"Assignment 1","assignment_id":'$firstassignmentid',"grade":null,"comment":null,"grader_name":null,"grader_email":null},
    {"assignment_name":"Assignment 2","assignment_id":'$secondassignmentid',"grade":null,"comment":null,"grader_name":null,"grader_email":null}
]'

json_exact_match_test "Request the Bob's assignment grades from Eugene" "$info" "$expected" "assignment_id"

# --------------------------------------------------------------------

fail_test "Request all course grades from Eugene (parent)" \
    -X POST "$API_URL/get_all_course_grades?course_id=$mathcourseid" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request Charlie's assignment grades from Eugene" \
    -X POST "$API_URL/get_student_course_grades?course_id=$mathcourseid&student_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

./backend/tests/dbreset.sh || exit 1
