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

login_and_get_token "Login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

fail_test "Request the list of all users from Alice" \
    -X GET "$API_URL/get_all_users" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

fail_test "Request the list of all courses from Alice" \
    -X GET "$API_URL/get_all_courses" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

admins=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_admins")

expected='[
    {"email":"admin","name":"admin"}
]'

json_exact_match_test "Request the list of admins from Alice" "$admins" "$expected" "email"

# --------------------------------------------------------------------

login_and_get_token "Login as Admin" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin\",\"password\":\"admin\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_user_info")

expected='
    {"email":"admin","name":"admin"}
'

json_exact_match_test "Get the admin's name" "$info" "$expected" "email"

# --------------------------------------------------------------------

users=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_all_users")

expected='[
    {"email":"admin","name":"admin"},
    {"email":"alice@example.com","name":"Alice"}
]'

json_exact_match_test "Request the list of all users from Admin" "$users" "$expected" "email"

# --------------------------------------------------------------------

admins=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_admins")

expected='[
    {"email":"admin","name":"admin"}
]'

json_exact_match_test "Request the list of admins from Admin" "$admins" "$expected" "email"

# --------------------------------------------------------------------

courses=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_all_courses")

expected='[]'

json_exact_match_test "Request the list of courses from Admin" "$courses" "$expected" "course_id"

# --------------------------------------------------------------------

success_test "Giving admin rights to Alice by Admin" \
    -X PATCH "$API_URL/give_admin_permissions?object_email=alice@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

admins=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_admins")

expected='[
    {"email":"admin","name":"admin"},
    {"email":"alice@example.com","name":"Alice"}
]'

json_exact_match_test "Request the list of admins from Admin" "$admins" "$expected" "email"

# --------------------------------------------------------------------

success_test "Removing Alice account from Admin" \
    -X DELETE "$API_URL/remove_user?deleted_user_email=alice@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

./backend/tests/dbreset.sh || exit 1
