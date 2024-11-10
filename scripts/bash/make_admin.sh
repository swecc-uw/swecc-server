#!/bin/bash

# check username provided
if [ -z "$1" ]; then
    echo "Username argument is required."
    exit 1
else
    username="$1"
fi

# queries
SQL_QUERY_GROUP="INSERT INTO auth_group (id, name) VALUES (2, 'is_admin') ON CONFLICT DO NOTHING;"
SQL_QUERY_USER_GROUP="INSERT INTO members_user_groups (user_id, group_id) VALUES ((SELECT id FROM members_user WHERE username = '$username'), 2) ON CONFLICT DO NOTHING;"
SQL_QUERY="update members_user set is_superuser = 't' where username = '$username'; update members_user set is_staff = 't' where username = '$username';"

# execute
docker exec -it swecc-server-db-1 psql -U root postgres -c "$SQL_QUERY"
docker exec -it swecc-server-db-1 psql -U root postgres -c "$SQL_QUERY_GROUP"
docker exec -it swecc-server-db-1 psql -U root postgres -c "$SQL_QUERY_USER_GROUP"

echo "User '$username' is now an admin."