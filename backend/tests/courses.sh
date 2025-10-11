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

fail_test "Request to create the course with too short name" \
    -X POST "$API_URL/create_course?title=M&organization=Innopolis%20University" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the course with too long name" \
    -X POST "$API_URL/create_course?title=MathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMathMath&organization=Innopolis%20University" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the course with invalid name" \
    -X POST "$API_URL/create_course?title=M%24ath&organization=Innopolis%20University" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the course with too short organization" \
    -X POST "$API_URL/create_course?title=Math&organization=In" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the course with too long organization" \
    -X POST "$API_URL/create_course?title=Math&organization=Innopolis%20UniversityInnopolis%20UniversityInnopolis%20UniversityInnopolis%20UniversityInnopolis%20University" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the course with invalid organization" \
    -X POST "$API_URL/create_course?title=Math&organization=Innopolis%24University" \
    -H "Authorization: Bearer $TOKEN" \

noorgcourseid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_course?title=Math" | extract_field course_id)

echo "✓ Successful Create the course with no organization"

success_test "Remove the course with no organization" \
    -X DELETE "$API_URL/remove_course?course_id=$noorgcourseid" \
    -H "Authorization: Bearer $TOKEN" \

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

json_exact_match_test "Get Alice's role in course Math" "$info" "$expected" "is_instructor"

# --------------------------------------------------------------------

success_test "Set course emoji" \
    -X PUT "$API_URL/set_course_emoji?course_id=$mathcourseid&emoji_id=1" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Set course emoji with too large ID" \
    -X PUT "$API_URL/set_course_emoji?course_id=$mathcourseid&emoji_id=10000" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Set course emoji with negative ID" \
    -X PUT "$API_URL/set_course_emoji?course_id=$mathcourseid&emoji_id=-10" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_info?course_id=$mathcourseid")

expected='
    {"course_id":"'"$mathcourseid"'","title":"Math","instructor_email":"alice@example.com","instructor_name":"Alice","organization":"Innopolis University","emoji_id":1}
'

json_partial_match_test "Request the course info from Alice" "$info" "$expected" "course_id" "creation_time"

# --------------------------------------------------------------------

fail_test "Request to create the material with too short title" \
    -X POST "$API_URL/create_material?course_id=$mathcourseid&section_id=2&title=Ti&description=Lecture%20material%20description" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the material with too long title" \
    -X POST "$API_URL/create_material?course_id=$mathcourseid&section_id=2&title=TitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitle&description=Lecture%20material%20description" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the material with invalid title" \
    -X POST "$API_URL/create_material?course_id=$mathcourseid&section_id=2&title=Ti%24tle&description=Lecture%20material%20description" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the material with too short description" \
    -X POST "$API_URL/create_material?course_id=$mathcourseid&section_id=2&title=Title&description=De" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request to create the assignment with too short title" \
    -X POST "$API_URL/create_assignment?course_id=$mathcourseid&section_id=2&title=Ti&description=Lecture%20assignment%20description" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the assignment with too long title" \
    -X POST "$API_URL/create_assignment?course_id=$mathcourseid&section_id=2&title=TitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitleTitle&description=Lecture%20assignment%20description" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the assignment with invalid title" \
    -X POST "$API_URL/create_assignment?course_id=$mathcourseid&section_id=2&title=Ti%24tle&description=Lecture%20assignment%20description" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to create the assignment with too short description" \
    -X POST "$API_URL/create_assignment?course_id=$mathcourseid&section_id=2&title=Title&description=De" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

materialid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_material?course_id=$mathcourseid&section_id=2&title=Lecture%20material&description=Lecture%20material%20description" | extract_field material_id)

# --------------------------------------------------------------------

assignmentid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_assignment?course_id=$mathcourseid&section_id=2&title=Assignment%201&description=To%20do%20exercise%2010%20from%20the%20course%20book" | extract_field assignment_id)

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_feed?course_id=$mathcourseid")

expected='[
    {"course_id":"'"$mathcourseid"'","post_id":'$materialid',"section_id":2,"section_name":"General","section_order":0,"type":"mat","author":"alice@example.com"},
    {"course_id":"'"$mathcourseid"'","post_id":'$assignmentid',"section_id":2,"section_name":"General","section_order":0,"type":"ass","author":"alice@example.com"}
]'

json_partial_match_test "Request the course feed from Alice" "$info" "$expected" "post_id type" "creation_time"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_material?course_id=$mathcourseid&material_id=$materialid")

expected='
    {"course_id":"'"$mathcourseid"'","material_id":'$materialid',"section_id":2,"title":"Lecture material","description":"Lecture material description","author":"alice@example.com"}
'

json_partial_match_test "Request the material info from Alice" "$info" "$expected" "material_id" "creation_time"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_assignment?course_id=$mathcourseid&assignment_id=$assignmentid")

expected='
    {"course_id":"'"$mathcourseid"'","assignment_id":'$assignmentid',"section_id":2,"title":"Assignment 1","description":"To do exercise 10 from the course book","author":"alice@example.com"}
'

json_partial_match_test "Request the assignment info from Alice" "$info" "$expected" "assignment_id" "creation_time"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_assignments?course_id=$mathcourseid")

expected='[
    {"course_id":"'"$mathcourseid"'","assignment_id":'$assignmentid',"section_id":2,"title":"Assignment 1","description":"To do exercise 10 from the course book","author":"alice@example.com"}
]'

json_partial_match_test "Request the assignment info from Alice" "$info" "$expected" "assignment_id" "creation_time"

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

# --------------------------------------------------------------------

courses=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/available_courses")

expected='[]'

json_exact_match_test "Request the list of available courses from Bob" "$courses" "$expected" "course_id"

# --------------------------------------------------------------------

courses=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_instructor_courses")

expected='[]'

json_exact_match_test "Request the list of instructor courses from Bob" "$courses" "$expected" "course_id"

# --------------------------------------------------------------------

fail_test "Request the course info from Bob" \
    -X GET "$API_URL/get_course_info?course_id=$mathcourseid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request the course feed from Bob" \
    -X GET "$API_URL/get_course_feed?course_id=$mathcourseid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request the course material from Bob" \
    -X GET "$API_URL/get_material?course_id=$mathcourseid&material_id=$materialid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request the course assignment from Bob" \
    -X GET "$API_URL/get_assignment?course_id=$mathcourseid&assignment_id=$assignmentid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

engcourseid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_course?title=English&organization=Skyeng" | extract_field course_id)

success_test "Add a new section to Bob's course by Bob" \
    -X POST "$API_URL/create_section?course_id=$engcourseid&title=New%20Section" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_user_role?course_id=$engcourseid")

expected='
    {"is_instructor":true,"is_teacher":true,"is_student":false,"is_parent":false,"is_admin":false}
'

json_exact_match_test "Get the Bob's role in course English" "$info" "$expected" "is_instructor"

# --------------------------------------------------------------------

success_test "Invite Alice to Bob's course" \
    -X POST "$API_URL/invite_student?course_id=$engcourseid&student_email=alice@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

materialid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_material?course_id=$engcourseid&section_id=3&title=Lecture%20material&description=Lecture%20material%20description" | extract_field material_id)

# --------------------------------------------------------------------

assignmentid=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/create_assignment?course_id=$engcourseid&section_id=4&title=Assignment%201&description=To%20do%20exercise%2010%20from%20the%20course%20book" | extract_field assignment_id)

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_user_role?course_id=$engcourseid")

expected='
    {"is_instructor":false,"is_teacher":false,"is_student":true,"is_parent":false,"is_admin":false}
'

json_exact_match_test "Get Alice's role in course English" "$info" "$expected" "is_instructor"

# --------------------------------------------------------------------

courses=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/available_courses")

expected='[
    {"course_id":"'"$mathcourseid"'","title":"Math","organization":"Innopolis University","instructor_email":"alice@example.com","instructor_name":"Alice"},
    {"course_id":"'"$engcourseid"'","title":"English","organization":"Skyeng","instructor_email":"bob@example.com","instructor_name":"Bob"}
]'

json_partial_match_test "Request the list of available courses from Alice" "$courses" "$expected" "course_id" "creation_time emoji_id"

# --------------------------------------------------------------------

success_test "Change the order of available courses by Alice" \
    -X PUT "$API_URL/change_courses_order?new_order=$engcourseid&new_order=$mathcourseid" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to change the order of courses to repeating ones by Alice" \
    -X PUT "$API_URL/change_courses_order?new_order=$mathcourseid&new_order=$mathcourseid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

courses=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/available_courses")

expected='[
    {"course_id":"'"$engcourseid"'","title":"English","organization":"Skyeng","instructor_email":"bob@example.com","instructor_name":"Bob"},
    {"course_id":"'"$mathcourseid"'","title":"Math","organization":"Innopolis University","instructor_email":"alice@example.com","instructor_name":"Alice"}
]'

json_partial_match_test "Request the list of available courses from Alice" "$courses" "$expected" "course_id" "creation_time emoji_id"

# --------------------------------------------------------------------

courses=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_instructor_courses")

expected='[
    {"course_id":"'"$mathcourseid"'"}
]'

json_exact_match_test "Request the list of instructor courses from Alice" "$courses" "$expected" "course_id"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_feed?course_id=$engcourseid")

expected='[
    {"course_id":"'"$engcourseid"'","post_id":'$materialid',"section_id":3,"section_name":"General","section_order":0,"type":"mat","author":"bob@example.com"},
    {"course_id":"'"$engcourseid"'","post_id":'$assignmentid',"section_id":4,"section_name":"New Section","section_order":1,"type":"ass","author":"bob@example.com"}
]'

json_partial_match_test "Request the course feed from Alice" "$info" "$expected" "post_id type" "creation_time"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_material?course_id=$engcourseid&material_id=$materialid")

expected='
    {"course_id":"'"$engcourseid"'","material_id":'$materialid',"section_id":3,"title":"Lecture material","description":"Lecture material description","author":"bob@example.com"}
'

json_partial_match_test "Request the material info from Alice" "$info" "$expected" "material_id" "creation_time"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_assignment?course_id=$engcourseid&assignment_id=$assignmentid")

expected='
    {"course_id":"'"$engcourseid"'","assignment_id":'$assignmentid',"section_id":4,"title":"Assignment 1","description":"To do exercise 10 from the course book","author":"bob@example.com"}
'

json_partial_match_test "Request the assignment info from Alice" "$info" "$expected" "assignment_id" "creation_time"

# --------------------------------------------------------------------

fail_test "Request to delete Bob's course by Alice" \
    -X DELETE "$API_URL/remove_course?course_id=$engcourseid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request to delete the material in Bob's course by Alice" \
    -X DELETE "$API_URL/remove_material?course_id=$engcourseid&material_id=$materialid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request to delete the assignment in Bob's course by Alice" \
    -X DELETE "$API_URL/remove_assignment?course_id=$engcourseid&assignment_id=$assignmentid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

# --------------------------------------------------------------------

success_test "Delete the material in Bob's course by Bob" \
    -X DELETE "$API_URL/remove_material?course_id=$engcourseid&material_id=$materialid" \
    -H "Authorization: Bearer $TOKEN" \

success_test "Delete the assignment in Bob's course by Bob" \
    -X DELETE "$API_URL/remove_assignment?course_id=$engcourseid&assignment_id=$assignmentid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request to delete the deleted material in Bob's course by Bob" \
    -X DELETE "$API_URL/remove_material?course_id=$engcourseid&material_id=$materialid" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to delete the deleted assignment in Bob's course by Bob" \
    -X DELETE "$API_URL/remove_assignment?course_id=$engcourseid&assignment_id=$assignmentid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_course_feed?course_id=$engcourseid")

expected='[
    {"course_id":"'"$engcourseid"'","post_id":null,"section_id":3,"section_name":"General","section_order":0,"type":null,"author":null},
    {"course_id":"'"$engcourseid"'","post_id":null,"section_id":4,"section_name":"New Section","section_order":1,"type":null,"author":null}
]'

json_partial_match_test "Request the empty course feed from Bob" "$info" "$expected" "post_id type" "creation_time"

# --------------------------------------------------------------------

fail_test "Request to get the removed material by Bob" \
    -X GET "$API_URL/get_material?course_id=$engcourseid&material_id=$materialid" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to get the removed assignment by Bob" \
    -X GET "$API_URL/get_assignment?course_id=$engcourseid&assignment_id=$assignmentid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

fail_test "Request to get the removed material by Alice" \
    -X GET "$API_URL/get_material?course_id=$engcourseid&material_id=$materialid" \
    -H "Authorization: Bearer $TOKEN" \

fail_test "Request to get the removed assignment by Alice" \
    -X GET "$API_URL/get_assignment?course_id=$engcourseid&assignment_id=$assignmentid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

# --------------------------------------------------------------------

success_test "Delete Bob's course" \
    -X DELETE "$API_URL/remove_course?course_id=$engcourseid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request to get the feed of the removed course by Bob" \
    -X GET "$API_URL/get_course_feed?course_id=$engcourseid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

success_test "Removing Bob's account from Bob" \
    -X DELETE "$API_URL/remove_user?deleted_user_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

courses=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/available_courses")

expected='[
    {"course_id":"'"$mathcourseid"'","title":"Math","organization":"Innopolis University","instructor_email":"alice@example.com","instructor_name":"Alice"}
]'

json_partial_match_test "Request the list of available courses from Alice" "$courses" "$expected" "course_id" "creation_time emoji_id"

# --------------------------------------------------------------------

fail_test "Request to get the feed of the removed course" \
    -X GET "$API_URL/get_course_feed?course_id=$engcourseid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

success_test "Delete Alice's course" \
    -X DELETE "$API_URL/remove_course?course_id=$mathcourseid" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

./backend/tests/dbreset.sh || exit 1
