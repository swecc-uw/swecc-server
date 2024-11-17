set "SQL_QUERY= select id, username from members_user"

docker exec -it swecc-server-db-1 psql -U root postgres -c "%SQL_QUERY%"
