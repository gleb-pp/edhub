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

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

mathcourseid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_course?title=Math&organization=Innopolis%20University" | extract_field course_id)

# --------------------------------------------------------------------

success_test "Invite Bob to Alice's Math course" \
    -X POST "$API_URL/invite_student?course_id=$mathcourseid&student_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_feed?course_id=$mathcourseid")

expected='[
    {"course_id":"'"$mathcourseid"'","post_id":null,"section_id":1,"section_name":"General","section_order":0,"type":null,"author":null}
]'

json_partial_match_test "Request the course feed from Alice" "$info" "$expected" "post_id type" "creation_time"

# --------------------------------------------------------------------

fail_test "Request to create the section with too short name" \
    -X POST "$API_URL/create_section?course_id=$mathcourseid&title=N" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the section with too long name" \
    -X POST "$API_URL/create_section?course_id=$mathcourseid&title=MathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMath" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the section with invalid name" \
    -X POST "$API_URL/create_section?course_id=$mathcourseid&title=M%24ath" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Add a new section to Math course by Alice" \
    -X POST "$API_URL/create_section?course_id=$mathcourseid&title=New%20Section" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

materialid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_material?course_id=$mathcourseid&section_id=2&title=Lecture%20material&description=Lecture%20material%20description" | extract_field material_id)

# --------------------------------------------------------------------

assignmentid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_assignment?course_id=$mathcourseid&section_id=1&title=Assignment%201&description=To%20do%20exercise%2010%20from%20the%20course%20book" | extract_field assignment_id)

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_feed?course_id=$mathcourseid")

expected='[
    {"course_id":"'"$mathcourseid"'","post_id":'$assignmentid',"section_id":1,"section_name":"General","section_order":0,"type":"ass","author":"alice@example.com"},
    {"course_id":"'"$mathcourseid"'","post_id":'$materialid',"section_id":2,"section_name":"New Section","section_order":1,"type":"mat","author":"alice@example.com"}
]'

json_partial_match_test "Request the course feed from Alice" "$info" "$expected" "post_id type" "creation_time"

# --------------------------------------------------------------------

success_test "Change the section order in Math course by Alice" \
    -X PUT "$API_URL/change_section_order?course_id=$mathcourseid&new_order=2&new_order=1" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_feed?course_id=$mathcourseid")

expected='[
    {"course_id":"'"$mathcourseid"'","post_id":'$materialid',"section_id":2,"section_name":"New Section","section_order":0,"type":"mat","author":"alice@example.com"},
    {"course_id":"'"$mathcourseid"'","post_id":'$assignmentid',"section_id":1,"section_name":"General","section_order":1,"type":"ass","author":"alice@example.com"}
]'

json_partial_match_test "Request the course feed from Alice" "$info" "$expected" "post_id type" "creation_time"

# --------------------------------------------------------------------

success_test "Delete the material in Math course by Alice" \
    -X DELETE "$API_URL/remove_material?course_id=$mathcourseid&material_id=$materialid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_feed?course_id=$mathcourseid")

expected='[
    {"course_id":"'"$mathcourseid"'","post_id":null,"section_id":2,"section_name":"New Section","section_order":0,"type":null,"author":null},
    {"course_id":"'"$mathcourseid"'","post_id":'$assignmentid',"section_id":1,"section_name":"General","section_order":1,"type":"ass","author":"alice@example.com"}
]'

json_partial_match_test "Request the course feed from Alice" "$info" "$expected" "post_id type" "creation_time"

# --------------------------------------------------------------------

success_test "Remove the section from the Math course by Alice" \
    -X DELETE "$API_URL/remove_section?course_id=$mathcourseid&section_id=1" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_feed?course_id=$mathcourseid")

expected='[
    {"course_id":"'"$mathcourseid"'","post_id":null,"section_id":2,"section_name":"New Section","section_order":0,"type":null,"author":null}
]'

json_partial_match_test "Request the course feed from Alice" "$info" "$expected" "post_id type" "creation_time"

# --------------------------------------------------------------------

fail_test "Request to remove the last section from the Math course by Alice" \
    -X DELETE "$API_URL/remove_section?course_id=$mathcourseid&section_id=2" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Add a new section to Math course by Alice" \
    -X POST "$API_URL/create_section?course_id=$mathcourseid&title=One%20More%20Section" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

# --------------------------------------------------------------------

fail_test "Add a new section to Math course by Bob" \
    -X POST "$API_URL/create_section?course_id=$mathcourseid&title=Totally%20New%20Section" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to change the section order in Math course by Bob" \
    -X PUT "$API_URL/change_section_order?course_id=$mathcourseid&new_order=1&new_order=2" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to remove the section from the Math course by Bob" \
    -X DELETE "$API_URL/remove_section?course_id=$mathcourseid&section_id=2" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

./backend/tests/dbreset.sh || exit 1
