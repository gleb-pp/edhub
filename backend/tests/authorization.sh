#!/bin/bash
set -euo pipefail

API_URL="http://localhost:8000"

source ./backend/tests/common_functions.sh

# --------------------------------------------------------------------

fail_test "Registration with incorrect email" \
    -X POST "$API_URL/create_user" \
    -H "Content-Type: application/json" \
    -d '{"email":"mailmail","password":"Password123!","name":"Alice"}'

# --------------------------------------------------------------------

fail_test "Registration with too long name" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\",\"name\":\"AliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAliceAlice\"}"

# --------------------------------------------------------------------

fail_test "Registration with invalid name (dollar sign)" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\",\"name\":\"Alice%24Alice\"}"

# --------------------------------------------------------------------

fail_test "Registration with invalid name (starts with digits)" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\",\"name\":\"2025Alice\"}"

# --------------------------------------------------------------------

fail_test "Registration with weak password" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"pwd\",\"name\":\"Alice\"}"

# --------------------------------------------------------------------

success_test "Correct registration of Alice" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\",\"name\":\"Alice\"}"

# --------------------------------------------------------------------

fail_test "Registration with existing email" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"Password123!\",\"name\":\"Bob\"}"

# --------------------------------------------------------------------

fail_test "Login with non-existing email" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"randomemail@example.com\",\"password\":\"Password123!\"}"

# --------------------------------------------------------------------

fail_test "Login with incorrect password" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"Password123!\"}"

# --------------------------------------------------------------------

login_and_get_token "Correct login as Alice" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\"}"

# --------------------------------------------------------------------

info=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$API_URL/get_user_info")

expected='
    {"email":"alice@example.com","name":"Alice"}
'

json_exact_match_test "Get Alice's name" "$info" "$expected" "email"

# --------------------------------------------------------------------

fail_test "Changing password with incorrect original password" \
    -X PATCH "$API_URL/change_password" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"Password123!\",\"new_password\":\"NewPass456!\"}"

# --------------------------------------------------------------------

success_test "Correct changing password" \
    -X PATCH "$API_URL/change_password" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"alicePass123!\",\"new_password\":\"AlicePass123!\"}"

# --------------------------------------------------------------------

success_test "Correct registration of Bob" \
    -X POST $API_URL/create_user \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\",\"name\":\"Bob\"}"

# --------------------------------------------------------------------

fail_test "Removing Bob account from Alice" \
    -X DELETE "$API_URL/remove_user?deleted_user_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

success_test "Removing Alice account from Alice" \
    -X DELETE "$API_URL/remove_user?deleted_user_email=alice@example.com" \
    -H "Authorization: Bearer $TOKEN" \

# --------------------------------------------------------------------

login_and_get_token "Correct login as Bob" \
    -X POST $API_URL/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"bob@example.com\",\"password\":\"bobPass123!\"}"

# --------------------------------------------------------------------

success_test "Removing Bob account from Bob" \
    -X DELETE "$API_URL/remove_user?deleted_user_email=bob@example.com" \
    -H "Authorization: Bearer $TOKEN" \
