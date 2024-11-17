set "SQL_QUERY= insert into interview_interviewpool select id from members_user"

docker exec -it swecc-server-db-1 psql -U root postgres -c "%SQL_QUERY%"
