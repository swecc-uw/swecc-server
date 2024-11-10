#!/bin/bash

# generate a random string of specified length
generate_random_string() {
    local length=$1
    local charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    local result=""
    for ((i=0; i<length; i++)); do
        local random_index=$((RANDOM % ${#charset}))
        result+="${charset:$random_index:1}"
    done
    echo "$result"
}

# username/email
random_string=$(generate_random_string 10)

# check if username argument passed, otherwise use random_string
if [ -z "$1" ]; then
    test_username="$random_string"
else
    test_username="$1"
fi

# set vars
hashed_pw="pbkdf2_sha256\$600000\$BjdYGzJ9HB5rWVdRnLRr5l\$WblHaqgKgjitB2svIbbTKuVe5BGe2p+7boYh0trY3NE="
test_firstname="$test_username"
test_lastname="EJ"
email="${random_string}@uw.edu"
discord_id="123456789"

# generate psql timestamp
# ex: 2024-09-17 19:24:03.742688+00
date_join="2024-09-17 19:24:03.742688+00"

# SQL queries
SQL_QUERY="INSERT INTO members_user (username, first_name, last_name, email, discord_username, discord_id, password, is_superuser, is_staff, is_active, date_joined, created) VALUES ('$test_username', '$test_firstname', '$test_lastname', '$email', '$random_string', '$discord_id', '$hashed_pw', 'f', 'f', 't', '$date_join', '$date_join');"
SQL_QUERY_INSERT_INTO_VERIFIED_TABLE="INSERT INTO auth_group (id, name) VALUES (1, 'verified') ON CONFLICT DO NOTHING;"
SQL_QUERY_INSERT_INTO_USER_GROUP_TABLE="INSERT INTO members_user_groups (user_id, group_id) VALUES ((SELECT id FROM members_user WHERE username = '$test_username'), 1) ON CONFLICT DO NOTHING;"

# exec queries
docker exec -it swecc-server-db-1 psql -U root postgres -c "$SQL_QUERY"
docker exec -it swecc-server-db-1 psql -U root postgres -c "$SQL_QUERY_INSERT_INTO_VERIFIED_TABLE"
docker exec -it swecc-server-db-1 psql -U root postgres -c "$SQL_QUERY_INSERT_INTO_USER_GROUP_TABLE"

echo "User created successfully. Username: $test_username, Email: $email"