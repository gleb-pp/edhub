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

success_test "Invite Bob to Alice's course as a student" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Invite Charlie to Alice's course as Bob's parent" \
    -X POST "$API_URL/invite_parent?course_id=$mathcourseid&student_email=bob@example.com&parent_email=charlie@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

assignmentid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_assignment?course_id=$mathcourseid&section_id=1&title=Assignment%201&description=To%20do%20exercise%2010%20from%20the%20course%20book" | extract_field assignment_id)

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_feed?course_id=$mathcourseid")

expected='[
    {"course_id":"'"$mathcourseid"'","post_id":'$assignmentid',"section_id":1,"section_name":"General","section_order":0,"type":"ass","author":"alice@example.com"}
]'

json_partial_match_test "Request the course feed from Bob" "$info" "$expected" "post_id type" "creation_time"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_assignment?course_id=$mathcourseid&assignment_id=$assignmentid")

expected='
    {"course_id":"'"$mathcourseid"'","assignment_id":'$assignmentid',"section_id":1,"title":"Assignment 1","description":"To do exercise 10 from the course book","author":"alice@example.com"}
'

json_partial_match_test "Request the assignment info from Bob" "$info" "$expected" "assignment_id" "creation_time"

# --------------------------------------------------------------------

fail_test "Request to submit the assignment with too short submission_text" \
    -X PUT "$API_URL/submit_assignment?course_id=$mathcourseid&assignment_id=$assignmentid&submission_text=An" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

success_test "Submit assignment as Bob" \
    -X PUT "$API_URL/submit_assignment?course_id=$mathcourseid&assignment_id=$assignmentid&submission_text=The%20answer%20is%2010" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_submission?course_id=$mathcourseid&assignment_id=$assignmentid&student_email=bob@example.com")

expected='
    {"course_id":"'"$mathcourseid"'","assignment_id":'$assignmentid',"student_email":"bob@example.com","student_name":"Bob","submission_text":"The answer is 10","grade":null,"comment":null,"gradedby_email":null,"gradedby_name":null}
'

json_partial_match_test "Request the submission details from Bob" "$info" "$expected" "assignment_id" "submission_time last_modification_time"

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_assignment_submissions?course_id=$mathcourseid&assignment_id=$assignmentid")

expected='[
    {"course_id":"'"$mathcourseid"'","assignment_id":'$assignmentid',"student_email":"bob@example.com","student_name":"Bob","submission_text":"The answer is 10","grade":null,"comment":null,"gradedby_email":null,"gradedby_name":null}
]'

json_partial_match_test "Request the list of assignment submissions by Alice" "$info" "$expected" "assignment_id" "submission_time last_modification_time"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_submission?course_id=$mathcourseid&assignment_id=$assignmentid&student_email=bob@example.com")

expected='
    {"course_id":"'"$mathcourseid"'","assignment_id":'$assignmentid',"student_email":"bob@example.com","student_name":"Bob","submission_text":"The answer is 10","grade":null,"comment":null,"gradedby_email":null,"gradedby_name":null}
'

json_partial_match_test "Request the submission details by Alice" "$info" "$expected" "assignment_id" "submission_time last_modification_time"

# --------------------------------------------------------------------

success_test "Grade submission by Alice" \
    -X PUT "$API_URL/grade_submission?course_id=$mathcourseid&assignment_id=$assignmentid&student_email=bob@example.com&grade=5&comment=Good%20job" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_submission?course_id=$mathcourseid&assignment_id=$assignmentid&student_email=bob@example.com")

expected='
    {"course_id":"'"$mathcourseid"'","assignment_id":'$assignmentid',"student_email":"bob@example.com","student_name":"Bob","submission_text":"The answer is 10","grade":5,"comment":"Good job","gradedby_email":"alice@example.com","gradedby_name":"Alice"}
'

json_partial_match_test "Request the submission details by Alice" "$info" "$expected" "assignment_id" "submission_time last_modification_time"

# --------------------------------------------------------------------

login_and_get_token "Login as Charlie" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"charlie@example.com\",\"password\":\"charliePass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_submission?course_id=$mathcourseid&assignment_id=$assignmentid&student_email=bob@example.com")

expected='
    {"course_id":"'"$mathcourseid"'","assignment_id":'$assignmentid',"student_email":"bob@example.com","student_name":"Bob","submission_text":"The answer is 10","grade":5,"comment":"Good job","gradedby_email":"alice@example.com","gradedby_name":"Alice"}
'

json_partial_match_test "Request the submission details by Charlie" "$info" "$expected" "assignment_id" "submission_time last_modification_time"

# --------------------------------------------------------------------

./backend/tests/dbreset.sh || exit 1
